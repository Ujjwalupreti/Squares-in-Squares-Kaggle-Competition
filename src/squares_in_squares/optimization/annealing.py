"""Simulated annealing with configurable schedule and acceptance.

Standard acceptance rule for worse candidates:
    p = exp(-(J_new - J_old) / T)

where T is the current temperature and J is the search objective.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

from .objective import compute_objective
from .moves import random_move
from ..validation.packing_validator import validate_packing_geometry
from ..geometry.sat import DEFAULT_SAT_TOLERANCE


@dataclass
class AnnealingResult:
    """Result of a simulated annealing run."""
    best_squares: np.ndarray | None = None
    best_L: float = float('inf')
    best_score: float = float('inf')
    best_valid: bool = False
    iterations: int = 0
    accepted: int = 0
    improved: int = 0
    feasible_found: int = 0
    runtime_seconds: float = 0.0
    final_temperature: float = 0.0
    move_stats: dict[str, dict[str, int]] = field(default_factory=dict)


def simulated_annealing(
    n: int,
    initial_squares: np.ndarray,
    initial_temp: float = 1.0,
    cooling_rate: float = 0.9999,
    min_temp: float = 1e-6,
    max_iterations: int = 100_000,
    time_limit: float = 60.0,
    translate_step: float = 0.1,
    rotate_step: float = 0.1,
    overlap_lambda: float = 1000.0,
    boundary_prob: float = 0.2,
    seed: int = 42,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
    move_decay: float = 0.999,
) -> AnnealingResult:
    """Run simulated annealing optimization.

    Maintains separate tracking of:
    - Current search state (may be infeasible)
    - Best feasible incumbent (validated independently)

    Args:
        n: puzzle size.
        initial_squares: starting packing (n, 3).
        initial_temp: starting temperature.
        cooling_rate: multiplicative cooling factor per iteration.
        min_temp: stopping temperature.
        max_iterations: maximum number of iterations.
        time_limit: wall-clock time limit in seconds.
        translate_step: initial max translation.
        rotate_step: initial max rotation.
        overlap_lambda: weight for overlap penalty.
        boundary_prob: probability of boundary-focused move.
        seed: random seed.
        tolerance: SAT tolerance.
        move_decay: multiplicative decay for step sizes.

    Returns:
        AnnealingResult with the best validated solution.
    """
    rng = np.random.default_rng(seed)
    result = AnnealingResult()

    start_time = time.time()

    # Evaluate initial state
    current = initial_squares.copy()
    current_J, current_L, current_P = compute_objective(current, overlap_lambda)

    # Initialize best feasible from initial if it's valid
    vr = validate_packing_geometry(current, n, tolerance=tolerance)
    if vr.valid:
        result.best_squares = current.copy()
        result.best_L = vr.container_length
        result.best_score = vr.score
        result.best_valid = True
        result.feasible_found += 1

    T = initial_temp
    t_step = translate_step
    r_step = rotate_step

    for iteration in range(max_iterations):
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            break

        # Check temperature
        if T < min_temp:
            break

        # Generate candidate
        candidate, move_name = random_move(
            current, rng,
            translate_step=t_step,
            rotate_step=r_step,
            boundary_prob=boundary_prob,
        )
        if move_name not in result.move_stats:
            result.move_stats[move_name] = {"proposed": 0, "accepted": 0, "improved": 0}
        result.move_stats[move_name]["proposed"] += 1

        # Evaluate candidate
        cand_J, cand_L, cand_P = compute_objective(candidate, overlap_lambda)

        # Acceptance decision
        delta = cand_J - current_J
        accept = False
        if delta <= 0:
            accept = True
        else:
            p = math.exp(-delta / T) if T > 0 else 0
            if rng.random() < p:
                accept = True

        if accept:
            current = candidate
            current_J = cand_J
            current_L = cand_L
            current_P = cand_P
            result.accepted += 1
            result.move_stats[move_name]["accepted"] += 1

            # Check feasibility for incumbent update
            if current_P < 1e-15:  # Likely feasible
                vr = validate_packing_geometry(current, n, tolerance=tolerance)
                if vr.valid:
                    result.feasible_found += 1
                    if vr.container_length < result.best_L:
                        result.best_squares = current.copy()
                        result.best_L = vr.container_length
                        result.best_score = vr.score
                        result.best_valid = True
                        result.improved += 1
                        result.move_stats[move_name]["improved"] += 1

        # Cool down
        T *= cooling_rate
        t_step *= move_decay
        r_step *= move_decay

        result.iterations = iteration + 1

    result.runtime_seconds = time.time() - start_time
    result.final_temperature = T

    return result
