"""Multi-start search orchestration.

Runs multiple optimization attempts from different starting
configurations and keeps the best validated result.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .annealing import simulated_annealing, AnnealingResult
from .local_search import local_refinement
from ..packing.grid import grid_packing
from ..packing.staggered import staggered_packing
from ..packing.rotated_patterns import corner_center_rotated_packing
from ..validation.packing_validator import validate_packing_geometry
from ..geometry.sat import DEFAULT_SAT_TOLERANCE


@dataclass
class RestartResult:
    """Result of multi-start optimization."""
    best_squares: np.ndarray | None = None
    best_L: float = float('inf')
    best_score: float = float('inf')
    best_valid: bool = False
    total_restarts: int = 0
    total_iterations: int = 0
    total_runtime: float = 0.0
    best_strategy: str = ""


def multi_start_optimize(
    n: int,
    num_restarts: int = 3,
    sa_kwargs: dict | None = None,
    refine: bool = True,
    refine_kwargs: dict | None = None,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
    incumbent: np.ndarray | None = None,
) -> RestartResult:
    """Run optimization with multiple starts.

    Tries different initial configurations:
    0. Existing best incumbent (if provided)
    1. Grid packing
    2. Staggered packing
    3. Specialized rotated pattern
    4+ Perturbations

    Args:
        n: puzzle size.
        num_restarts: number of restarts.
        sa_kwargs: keyword arguments for simulated_annealing.
        refine: whether to apply local refinement after annealing.
        refine_kwargs: keyword arguments for local_refinement.
        tolerance: SAT tolerance.
        incumbent: existing best validated packing (n, 3).

    Returns:
        RestartResult with the best validated solution across all restarts.
    """
    result = RestartResult()
    sa_kwargs = sa_kwargs or {}
    refine_kwargs = refine_kwargs or {}

    # Pre-populate with incumbent if valid
    if incumbent is not None:
        vr = validate_packing_geometry(incumbent, n, tolerance=tolerance)
        if vr.valid:
            result.best_squares = incumbent.copy()
            result.best_L = vr.container_length
            result.best_score = vr.score
            result.best_valid = True
            result.best_strategy = "incumbent"

    # Generate initial configurations
    starters: list[tuple[str, np.ndarray]] = []
    if incumbent is not None:
        starters.append(("incumbent", incumbent.copy()))
    starters.append(("grid", grid_packing(n)))
    starters.append(("staggered", staggered_packing(n)))
    rot_cand = corner_center_rotated_packing(n)
    if rot_cand is not None:
        starters.append(("rotated_pattern", rot_cand))

    for restart_idx in range(num_restarts):
        if restart_idx < len(starters):
            strategy_name, initial = starters[restart_idx]
        else:
            # Use grid with random seed
            strategy_name = f"grid_restart_{restart_idx}"
            initial = grid_packing(n)

        # Run simulated annealing
        seed = sa_kwargs.get("seed", 42) + restart_idx
        clean_sa = {k: v for k, v in sa_kwargs.items() if k not in ("seed", "tolerance")}
        ar = simulated_annealing(
            n=n,
            initial_squares=initial,
            seed=seed,
            tolerance=tolerance,
            **clean_sa,
        )

        result.total_iterations += ar.iterations
        result.total_runtime += ar.runtime_seconds
        result.total_restarts += 1

        # Apply local refinement if we have a feasible solution
        if refine and ar.best_valid and ar.best_squares is not None:
            clean_refine = {k: v for k, v in refine_kwargs.items() if k not in ("seed", "tolerance")}
            refined, refined_L, ref_iters = local_refinement(
                n=n,
                squares=ar.best_squares,
                seed=seed + 1000,
                tolerance=tolerance,
                **clean_refine,
            )
            # Validate refined solution
            vr = validate_packing_geometry(refined, n, tolerance=tolerance)
            if vr.valid and vr.container_length < ar.best_L:
                ar.best_squares = refined
                ar.best_L = vr.container_length
                ar.best_score = vr.score
                ar.best_valid = True

        # Update global best
        if ar.best_valid and ar.best_L < result.best_L:
            result.best_squares = ar.best_squares
            result.best_L = ar.best_L
            result.best_score = ar.best_score
            result.best_valid = True
            result.best_strategy = strategy_name

    return result
