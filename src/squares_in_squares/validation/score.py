"""Score calculation for the Squares in Squares competition.

Per-puzzle score: score(n) = L / sqrt(n) - 1
where L is the enclosing container side length.
Lower is better.
"""

from __future__ import annotations

import math

import numpy as np

from ..geometry.bounds import container_side_length


def puzzle_score(n: int, L: float) -> float:
    """Compute the per-puzzle score.

    Args:
        n: number of squares (puzzle size).
        L: container side length.

    Returns:
        score = L / sqrt(n) - 1. Lower is better.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    if not math.isfinite(L) or L <= 0:
        raise ValueError(f"Container length must be positive and finite, got {L}")
    return L / math.sqrt(n) - 1.0


def puzzle_score_from_packing(n: int, squares: np.ndarray) -> float:
    """Compute the per-puzzle score directly from a packing.

    Args:
        n: puzzle size.
        squares: array of shape (n, 3).

    Returns:
        Competition score.
    """
    L = container_side_length(squares)
    return puzzle_score(n, L)


def aggregate_score(scores: list[float]) -> float:
    """Compute the aggregate score over multiple puzzles.

    Args:
        scores: list of per-puzzle scores.

    Returns:
        Sum of all scores.
    """
    return sum(scores)
