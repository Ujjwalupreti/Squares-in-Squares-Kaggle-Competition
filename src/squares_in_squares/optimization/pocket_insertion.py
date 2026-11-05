"""Pocket Void Insertion and Continuous Relaxation for Transition Packing Growth.

Takes an incumbent high-density packing of size n (where L_n < ceil(sqrt(n))),
detects the largest unconstrained pocket or perimeter void, seeds square n+1,
and performs targeted local relaxation and HiGHS LP compaction to find
feasible non-grid packings for n+1 with container size L_{n+1} < ceil(sqrt(n+1)).
"""

from __future__ import annotations

import math
import numpy as np

from ..geometry.bounds import container_side_length, half_extents
from ..geometry.sat import squares_overlap, DEFAULT_SAT_TOLERANCE
from ..validation.packing_validator import validate_packing_geometry
from .contact_lp import contact_lp_squeeze


def find_best_void_candidate(
    squares: np.ndarray,
    target_L: float,
    grid_resolution: int = 25,
    angles: list[float] | None = None,
) -> tuple[float, float, float, int]:
    """Scan container grid to locate the insertion position with minimum overlap.

    Returns:
        (x, y, angle, overlap_count)
    """
    if angles is None:
        angles = [0.0, math.pi / 4.0, math.pi / 6.0, math.pi / 3.0]

    xs = np.linspace(0.6, target_L - 0.6, grid_resolution)
    ys = np.linspace(0.6, target_L - 0.6, grid_resolution)

    best_cand = (target_L / 2.0, target_L / 2.0, 0.0)
    min_overlaps = float('inf')

    n = squares.shape[0]
    sq_x = squares[:, 0]
    sq_y = squares[:, 1]
    sq_th = squares[:, 2]

    for x in xs:
        for y in ys:
            for th in angles:
                ov_cnt = 0
                for i in range(n):
                    # Broadphase AABB filter
                    if abs(sq_x[i] - x) > 1.45 or abs(sq_y[i] - y) > 1.45:
                        continue
                    if squares_overlap(x, y, th, sq_x[i], sq_y[i], sq_th[i], tolerance=1e-5):
                        ov_cnt += 1
                        if ov_cnt >= min_overlaps:
                            break

                if ov_cnt < min_overlaps:
                    min_overlaps = ov_cnt
                    best_cand = (x, y, th)
                    if min_overlaps == 0:
                        return x, y, th, 0

    return best_cand[0], best_cand[1], best_cand[2], int(min_overlaps)


def relax_inserted_packing(
    initial_squares: np.ndarray,
    target_n: int,
    max_steps: int = 150,
    learning_rate: float = 0.05,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
) -> tuple[np.ndarray | None, float]:
    """Relax positions using smooth soft-body repulsive gradient steps.

    Optimized for insertion: focuses repulsive forces on colliding squares
    and their immediate neighborhood for rapid convergence.
    """
    squares = initial_squares.copy()
    n = target_n

    angles = squares[:, 2]
    c = np.abs(np.cos(angles))
    s = np.abs(np.sin(angles))
    hx = 0.5 * (c + s)
    hy = 0.5 * (s + c)

    # The newly added square is at index n - 1
    new_idx = n - 1

    for step in range(max_steps):
        grad_x = np.zeros(n, dtype=np.float64)
        grad_y = np.zeros(n, dtype=np.float64)
        total_overlap = 0

        # Primary pass: check new square against all other squares
        colliding_with_new = []
        for i in range(n - 1):
            dx = squares[new_idx, 0] - squares[i, 0]
            dy = squares[new_idx, 1] - squares[i, 1]
            if abs(dx) >= hx[i] + hx[new_idx] or abs(dy) >= hy[i] + hy[new_idx]:
                continue
            if squares_overlap(
                squares[i, 0], squares[i, 1], squares[i, 2],
                squares[new_idx, 0], squares[new_idx, 1], squares[new_idx, 2],
                tolerance=tolerance,
            ):
                total_overlap += 1
                colliding_with_new.append(i)
                dist = math.hypot(dx, dy)
                fx = (dx / dist) * 0.06 if dist > 1e-6 else np.random.uniform(-0.02, 0.02)
                fy = (dy / dist) * 0.06 if dist > 1e-6 else np.random.uniform(-0.02, 0.02)
                grad_x[i] -= fx
                grad_x[new_idx] += fx
                grad_y[i] -= fy
                grad_y[new_idx] += fy

        # Secondary pass: only check neighbors of colliding squares
        for i in colliding_with_new:
            for j in range(i + 1, n - 1):
                dx = squares[j, 0] - squares[i, 0]
                dy = squares[j, 1] - squares[i, 1]
                if abs(dx) >= hx[i] + hx[j] or abs(dy) >= hy[i] + hy[j]:
                    continue
                if squares_overlap(
                    squares[i, 0], squares[i, 1], squares[i, 2],
                    squares[j, 0], squares[j, 1], squares[j, 2],
                    tolerance=tolerance,
                ):
                    total_overlap += 1
                    dist = math.hypot(dx, dy)
                    fx = (dx / dist) * 0.04 if dist > 1e-6 else np.random.uniform(-0.01, 0.01)
                    fy = (dy / dist) * 0.04 if dist > 1e-6 else np.random.uniform(-0.01, 0.01)
                    grad_x[i] -= fx
                    grad_x[j] += fx
                    grad_y[i] -= fy
                    grad_y[j] += fy

        if total_overlap == 0:
            vr = validate_packing_geometry(squares, n, tolerance=tolerance)
            if vr.valid:
                return squares, vr.container_length

        decay = 1.0 - (step / max_steps) * 0.5
        squares[:, 0] += grad_x * learning_rate * decay
        squares[:, 1] += grad_y * learning_rate * decay

    vr = validate_packing_geometry(squares, n, tolerance=tolerance)
    if vr.valid:
        return squares, vr.container_length

    return None, float('inf')


def grow_packing_by_insertion(
    incumbent_squares: np.ndarray,
    target_n: int,
    grid_resolution: int = 30,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
) -> tuple[np.ndarray | None, float, bool]:
    """Grow an incumbent packing from n-1 to target_n squares.

    Returns:
        (new_squares, container_length, success)
    """
    n_inc = incumbent_squares.shape[0]
    if n_inc != target_n - 1:
        raise ValueError(f"Incumbent has {n_inc} squares, expected {target_n - 1}")

    L_inc = container_side_length(incumbent_squares)
    k = int(math.ceil(math.sqrt(target_n)))

    # Scan for best void in incumbent container (expanded by tiny margin if needed)
    search_L = max(L_inc, math.sqrt(target_n) + 0.1)
    bx, by, bth, ovs = find_best_void_candidate(
        incumbent_squares, search_L, grid_resolution=grid_resolution
    )

    seeded = np.vstack([incumbent_squares, [bx, by, bth]])

    # If completely free of overlap, try LP squeeze immediately
    if ovs == 0:
        vr = validate_packing_geometry(seeded, target_n, tolerance=tolerance)
        if vr.valid:
            sq_lp, L_lp, _ = contact_lp_squeeze(seeded, target_n, tolerance=tolerance)
            if L_lp < k:
                return sq_lp, L_lp, True

    # Otherwise run local soft-body relaxation
    relaxed, L_rel = relax_inserted_packing(seeded, target_n, tolerance=tolerance)
    if relaxed is not None and L_rel < k:
        sq_lp, L_lp, _ = contact_lp_squeeze(relaxed, target_n, tolerance=tolerance)
        return sq_lp, L_lp, True

    return None, float('inf'), False

