"""End-to-end optimization orchestration.

Top-level solver that coordinates:
1. Initial candidate generation
2. Simulated annealing optimization
3. Local refinement
4. Incumbent validation and persistence
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from ..config import Config
from ..packing.grid import grid_packing
from ..validation.packing_validator import validate_packing_geometry
from ..validation.score import puzzle_score
from .annealing import simulated_annealing
from .local_search import local_refinement
from .restart import multi_start_optimize, RestartResult


@dataclass
class SolverResult:
    """Complete result of solving a single puzzle."""
    n: int
    squares: np.ndarray | None = None
    container_length: float = float('inf')
    score: float = float('inf')
    valid: bool = False
    strategy: str = ""
    seed: int = 0
    runtime_seconds: float = 0.0
    iterations: int = 0
    baseline_L: float = float('inf')
    baseline_score: float = float('inf')


def solve_puzzle(
    n: int,
    config: Config | None = None,
    use_optimization: bool = True,
) -> SolverResult:
    """Solve a single puzzle, returning the best validated solution.

    Args:
        n: puzzle size.
        config: project configuration.
        use_optimization: if False, return only the grid baseline.

    Returns:
        SolverResult with the best solution found.
    """
    if config is None:
        config = Config.default()

    result = SolverResult(n=n, seed=config.random_seed)
    start = time.time()

    # Always compute baseline
    baseline = grid_packing(n)
    vr = validate_packing_geometry(baseline, n, tolerance=config.sat_tolerance)
    if vr.valid:
        result.baseline_L = vr.container_length
        result.baseline_score = vr.score
        result.squares = baseline.copy()
        result.container_length = vr.container_length
        result.score = vr.score
        result.valid = True
        result.strategy = "grid"

    if not use_optimization or n == 1:
        result.runtime_seconds = time.time() - start
        return result

    # Run optimization
    sa_kwargs = dict(
        initial_temp=config.sa_initial_temp,
        cooling_rate=config.sa_cooling_rate,
        min_temp=config.sa_min_temp,
        max_iterations=config.sa_max_iterations,
        time_limit=config.sa_time_limit_seconds,
        translate_step=config.translate_step,
        rotate_step=config.rotate_step,
        overlap_lambda=config.overlap_lambda,
        seed=config.random_seed,
        tolerance=config.sat_tolerance,
        move_decay=config.move_decay,
    )

    refine_kwargs = dict(
        max_iterations=5000,
        initial_step=0.01,
        time_limit=10.0,
    )

    rr = multi_start_optimize(
        n=n,
        num_restarts=config.num_restarts,
        sa_kwargs=sa_kwargs,
        refine=True,
        refine_kwargs=refine_kwargs,
        tolerance=config.sat_tolerance,
    )

    result.iterations = rr.total_iterations
    result.runtime_seconds = time.time() - start

    # Update if optimization found something better
    if rr.best_valid and rr.best_L < result.container_length:
        result.squares = rr.best_squares
        result.container_length = rr.best_L
        result.score = rr.best_score
        result.valid = True
        result.strategy = rr.best_strategy

    return result
