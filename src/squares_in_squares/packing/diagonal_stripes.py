"""Parametric Diagonal Seam and Stripe Packing Generator.

Constructs multi-angle configurations consisting of a tilted diagonal seam
at angle theta = pi/4 (45 degrees) flanked by axis-aligned integer-spaced
triangular wings. Compacts slack using Contact-LP Squeeze to produce
feasible non-grid packings strictly below the integer ceiling L < k.
"""

from __future__ import annotations

import math
import numpy as np

from ..geometry.bounds import container_side_length
from ..geometry.sat import DEFAULT_SAT_TOLERANCE
from ..validation.packing_validator import validate_packing_geometry
from ..optimization.contact_lp import contact_lp_squeeze


def generate_diagonal_stripe_packing(
    n: int,
    stripe_count: int | None = None,
    theta: float = math.pi / 4.0,
    safety_margin: float = 1e-10,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
) -> tuple[np.ndarray | None, float, bool]:
    """Generate a diagonal stripe packing template for puzzle n.

    Args:
        n: target number of unit squares.
        stripe_count: number of tilted squares along main diagonal.
        theta: tilt angle in radians (default pi/4 = 45 degrees).
        safety_margin: positive buffer for separation constraints.
        tolerance: SAT tolerance.

    Returns:
        (squares, container_length, success)
    """
    k = int(math.ceil(math.sqrt(n)))
    # Estimate base container size
    base_L = math.sqrt(n) + 0.25
    if base_L >= k:
        base_L = k - 0.05

    # Rotated square extent
    diag_h = 0.5 * (abs(math.cos(theta)) + abs(math.sin(theta)))

    if stripe_count is None:
        # Heuristic: stripe count roughly proportional to k
        stripe_count = max(2, int((base_L - 2 * diag_h) / (1.0 / math.sqrt(2.0))) + 1)

    squares: list[list[float]] = []

    # 1. Place diagonal stripe squares
    step = 1.0 / math.sqrt(2.0)
    start_diag = diag_h + 0.1
    for i in range(stripe_count):
        cx = start_diag + i * step
        cy = start_diag + i * step
        if cx + diag_h <= base_L and cy + diag_h <= base_L:
            squares.append([cx, cy, theta])

    # 2. Fill lower-right and upper-left wings with axis-aligned unit squares (theta = 0)
    xs = np.arange(0.5, base_L - 0.5, 1.0)
    ys = np.arange(0.5, base_L - 0.5, 1.0)

    for x in xs:
        for y in ys:
            if len(squares) >= n:
                break
            # Check distance to diagonal line
            dist_to_diag = abs(y - x) / math.sqrt(2.0)
            if dist_to_diag >= diag_h + 0.55:
                squares.append([float(x), float(y), 0.0])
        if len(squares) >= n:
            break

    if len(squares) < n:
        # Template did not generate sufficient squares for target n
        return None, float('inf'), False

    # Truncate to exact n
    sq_arr = np.array(squares[:n], dtype=np.float64)

    # Initial SAT check
    vr = validate_packing_geometry(sq_arr, n, tolerance=tolerance)
    if not vr.valid:
        # Attempt recovery via soft-body relaxation or LP
        return None, float('inf'), False

    # Compact via HiGHS Contact-LP Squeeze
    compacted, L_comp, improved = contact_lp_squeeze(
        sq_arr, n, safety_margin=safety_margin, tolerance=tolerance
    )

    if L_comp < k:
        return compacted, L_comp, True

    return None, float('inf'), False

