"""Local refinement after global search.

Applies small moves around the best feasible layout to squeeze
additional improvement. Uses greedy hill-climbing (accept only
improvements) with decreasing step sizes.
"""

from __future__ import annotations

import time

import numpy as np

from .moves import translate_one, rotate_one, translate_rotate_one, find_boundary_square
from ..geometry.bounds import container_side_length, container_bounds
from ..geometry.sat import packing_has_overlap, DEFAULT_SAT_TOLERANCE
from ..validation.packing_validator import validate_packing_geometry


def local_refinement(
    n: int,
    squares: np.ndarray,
    max_iterations: int = 10_000,
    initial_step: float = 0.01,
    step_decay: float = 0.9995,
    min_step: float = 1e-6,
    time_limit: float = 30.0,
    seed: int = 42,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
) -> tuple[np.ndarray, float, int]:
    """Apply local refinement to improve a feasible packing.

    Combines:
    1. Targeted inward nudges for boundary-defining squares
    2. Small rotational adjustments
    3. Combined translation and rotation
    4. Adaptive step sizes with hill-climbing

    Args:
        n: puzzle size.
        squares: initial feasible packing (n, 3).
        max_iterations: iteration limit.
        initial_step: starting step size.
        step_decay: multiplicative decay per iteration.
        min_step: minimum step size before stopping.
        time_limit: wall-clock time limit.
        seed: random seed.
        tolerance: SAT tolerance.

    Returns:
        (best_squares, best_L, iterations_run)
    """
    rng = np.random.default_rng(seed)
    best = squares.copy()
    best_L = container_side_length(best)
    step = initial_step
    rot_step = initial_step
    start = time.time()
    iters = 0

    for it in range(max_iterations):
        if time.time() - start >= time_limit:
            break
        if step < min_step:
            break

        xmin, xmax, ymin, ymax = container_bounds(best)
        cx = (xmin + xmax) / 2.0
        cy = (ymin + ymax) / 2.0

        # Alternate between random square and boundary square
        is_boundary = rng.random() < 0.4
        if is_boundary:
            idx = find_boundary_square(best)
        else:
            idx = int(rng.integers(0, n))

        # Choose move operator
        move_kind = rng.integers(0, 3)

        if is_boundary and move_kind == 0:
            # Targeted inward nudge: move towards center (cx, cy)
            x_sign = -1.0 if best[idx, 0] > cx else 1.0
            y_sign = -1.0 if best[idx, 1] > cy else 1.0
            dx = float(rng.uniform(0.0, step) * x_sign)
            dy = float(rng.uniform(0.0, step) * y_sign)
            candidate = translate_one(best, idx, dx, dy)
        elif move_kind == 0:
            # Random translation
            dx = float(rng.uniform(-step, step))
            dy = float(rng.uniform(-step, step))
            candidate = translate_one(best, idx, dx, dy)
        elif move_kind == 1:
            # Small rotation
            dangle = float(rng.uniform(-rot_step, rot_step))
            candidate = rotate_one(best, idx, dangle)
        else:
            # Combined translation and rotation
            dx = float(rng.uniform(-step, step))
            dy = float(rng.uniform(-step, step))
            dangle = float(rng.uniform(-rot_step, rot_step))
            candidate = translate_rotate_one(best, idx, dx, dy, dangle)

        cand_L = container_side_length(candidate)
        if cand_L < best_L:
            # Verify feasibility with SAT
            has_overlap, _ = packing_has_overlap(candidate, tolerance=tolerance)
            if not has_overlap:
                best = candidate
                best_L = cand_L

        step *= step_decay
        rot_step *= step_decay
        iters = it + 1

    return best, best_L, iters
