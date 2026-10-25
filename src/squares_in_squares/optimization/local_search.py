"""Local refinement after global search.

Applies small moves around the best feasible layout to squeeze
additional improvement. Uses greedy hill-climbing (accept only
improvements) with decreasing step sizes.
"""

from __future__ import annotations

import time

import numpy as np

from .moves import translate_one, rotate_one, find_boundary_square
from ..geometry.bounds import container_side_length
from ..geometry.sat import packing_has_overlap, DEFAULT_SAT_TOLERANCE
from ..validation.packing_validator import validate_packing_geometry


def local_refinement(
    n: int,
    squares: np.ndarray,
    max_iterations: int = 10_000,
    initial_step: float = 0.01,
    step_decay: float = 0.999,
    min_step: float = 1e-6,
    time_limit: float = 30.0,
    seed: int = 42,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
) -> tuple[np.ndarray, float, int]:
    """Apply local refinement to improve a feasible packing.

    Only accepts moves that:
    1. Reduce the container side length.
    2. Maintain feasibility (no overlaps).

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
    start = time.time()
    iters = 0

    for it in range(max_iterations):
        if time.time() - start >= time_limit:
            break
        if step < min_step:
            break

        # Alternate between random square and boundary square
        if rng.random() < 0.3:
            idx = find_boundary_square(best)
        else:
            idx = rng.integers(0, n)

        # Try small translation
        dx = rng.uniform(-step, step)
        dy = rng.uniform(-step, step)
        candidate = translate_one(best, idx, dx, dy)

        cand_L = container_side_length(candidate)
        if cand_L < best_L:
            # Verify feasibility
            has_overlap, _ = packing_has_overlap(candidate, tolerance=tolerance)
            if not has_overlap:
                best = candidate
                best_L = cand_L

        step *= step_decay
        iters = it + 1

    return best, best_L, iters
