"""Linear Programming Contact Compaction (Contact-LP Squeeze) using HiGHS.

Given a packing with fixed (or candidate) angles, this module formulates
and solves a convex Linear Program over square translation coordinates
(x_i, y_i) and container side length L, compacting all internal slack
to machine precision under Separating Axis constraints.
"""

from __future__ import annotations

import math
import numpy as np
from scipy.optimize import linprog

from ..geometry.bounds import container_side_length, half_extents
from ..geometry.sat import DEFAULT_SAT_TOLERANCE
from ..validation.packing_validator import validate_packing_geometry


def get_separating_axis_constraint(
    xi: float, yi: float, thi: float,
    xj: float, yj: float, thj: float,
) -> tuple[float, float, float]:
    """Find the best separating axis between square i and square j.

    Returns:
        (ax, ay, req_dist) such that:
        ax * (xj - xi) + ay * (yj - yi) >= req_dist
    """
    ci, si = math.cos(thi), math.sin(thi)
    cj, sj = math.cos(thj), math.sin(thj)

    dx = xj - xi
    dy = yj - yi

    cos_diff = ci * cj + si * sj
    sin_diff = si * cj - ci * sj
    wj1 = 0.5 * (abs(cos_diff) + abs(sin_diff))
    wi3 = wj1

    # Axis 1: e_i1 = (ci, si)
    proj1 = dx * ci + dy * si
    req1 = 0.5 + wj1
    g1 = abs(proj1) - req1

    # Axis 2: e_i2 = (-si, ci)
    proj2 = -dx * si + dy * ci
    req2 = 0.5 + wj1
    g2 = abs(proj2) - req2

    # Axis 3: e_j1 = (cj, sj)
    proj3 = dx * cj + dy * sj
    req3 = wi3 + 0.5
    g3 = abs(proj3) - req3

    # Axis 4: e_j2 = (-sj, cj)
    proj4 = -dx * sj + dy * cj
    req4 = wi3 + 0.5
    g4 = abs(proj4) - req4

    candidates = [
        (g1, ci if proj1 >= 0 else -ci, si if proj1 >= 0 else -si, req1),
        (g2, -si if proj2 >= 0 else si, ci if proj2 >= 0 else -ci, req2),
        (g3, cj if proj3 >= 0 else -cj, sj if proj3 >= 0 else -sj, req3),
        (g4, -sj if proj4 >= 0 else sj, cj if proj4 >= 0 else -cj, req4),
    ]

    best_cand = max(candidates, key=lambda c: c[0])
    return best_cand[1], best_cand[2], best_cand[3]


def contact_lp_squeeze(
    squares: np.ndarray,
    n: int | None = None,
    contact_threshold: float = 0.15,
    safety_margin: float = 1e-10,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
) -> tuple[np.ndarray, float, bool]:
    """Squeeze container size L via convex Linear Programming using HiGHS.

    Args:
        squares: array of shape (n, 3) containing [x, y, angle].
        n: puzzle size (defaults to squares.shape[0]).
        contact_threshold: spatial threshold to include pairwise contact constraints.
        safety_margin: positive buffer added to contact distance (prevents false overlaps).
        tolerance: numerical tolerance for SAT verification.

    Returns:
        (compacted_squares, container_length, improved)
    """
    if n is None:
        n = squares.shape[0]

    orig_L = container_side_length(squares)
    angles = squares[:, 2]

    # Half extents
    c = np.abs(np.cos(angles))
    s = np.abs(np.sin(angles))
    hx = 0.5 * (c + s)
    hy = 0.5 * (s + c)

    # Variables:
    # index 0: L
    # index 1 .. n: x_0 .. x_{n-1}
    # index n+1 .. 2n: y_0 .. y_{n-1}
    num_vars = 1 + 2 * n

    # Minimize L
    c_obj = np.zeros(num_vars, dtype=np.float64)
    c_obj[0] = 1.0

    A_rows: list[np.ndarray] = []
    b_rows: list[float] = []

    # 1. Container boundary constraints for each square:
    # x_i - hx_i >= 0  =>  -x_i <= -hx_i
    # x_i + hx_i <= L  =>  x_i - L <= -hx_i
    # y_i - hy_i >= 0  =>  -y_i <= -hy_i
    # y_i + hy_i <= L  =>  y_i - L <= -hy_i
    for i in range(n):
        xi_var = 1 + i
        yi_var = 1 + n + i

        # -x_i <= -hx_i
        row = np.zeros(num_vars, dtype=np.float64)
        row[xi_var] = -1.0
        A_rows.append(row)
        b_rows.append(-hx[i])

        # x_i - L <= -hx_i
        row = np.zeros(num_vars, dtype=np.float64)
        row[xi_var] = 1.0
        row[0] = -1.0
        A_rows.append(row)
        b_rows.append(-hx[i])

        # -y_i <= -hy_i
        row = np.zeros(num_vars, dtype=np.float64)
        row[yi_var] = -1.0
        A_rows.append(row)
        b_rows.append(-hy[i])

        # y_i - L <= -hy_i
        row = np.zeros(num_vars, dtype=np.float64)
        row[yi_var] = 1.0
        row[0] = -1.0
        A_rows.append(row)
        b_rows.append(-hy[i])

    # 2. Pairwise contact separating axis constraints
    x = squares[:, 0]
    y = squares[:, 1]

    for i in range(n):
        xi, yi, hxi, hyi = x[i], y[i], hx[i], hy[i]
        for j in range(i + 1, n):
            # AABB broadphase filter
            if abs(x[j] - xi) >= hxi + hx[j] + contact_threshold:
                continue
            if abs(y[j] - yi) >= hyi + hy[j] + contact_threshold:
                continue

            ax, ay, req = get_separating_axis_constraint(
                xi, yi, angles[i],
                x[j], y[j], angles[j],
            )

            # Constraint: ax * (x_j - x_i) + ay * (y_j - y_i) >= req + safety_margin
            # => ax * x_i - ax * x_j + ay * y_i - ay * y_j <= -(req + safety_margin)
            row = np.zeros(num_vars, dtype=np.float64)
            row[1 + i] = ax
            row[1 + j] = -ax
            row[1 + n + i] = ay
            row[1 + n + j] = -ay
            A_rows.append(row)
            b_rows.append(-(req + safety_margin))

    A_ub = np.array(A_rows, dtype=np.float64)
    b_ub = np.array(b_rows, dtype=np.float64)

    bounds = [(1.0, orig_L + 1.0)] + [(0.0, orig_L + 1.0)] * (2 * n)

    res = linprog(
        c_obj,
        A_ub=A_ub,
        b_ub=b_ub,
        bounds=bounds,
        method="highs",
    )

    if not res.success:
        return squares.copy(), orig_L, False

    new_L = float(res.x[0])
    if new_L >= orig_L - 1e-8:
        return squares.copy(), orig_L, False

    new_x = res.x[1 : 1 + n]
    new_y = res.x[1 + n : 1 + 2 * n]

    candidate = np.zeros_like(squares)
    candidate[:, 0] = new_x
    candidate[:, 1] = new_y
    candidate[:, 2] = angles

    # Strict independent SAT validation
    vr = validate_packing_geometry(candidate, n, tolerance=tolerance)
    if vr.valid and vr.container_length < orig_L - 1e-8:
        return candidate, vr.container_length, True

    return squares.copy(), orig_L, False

