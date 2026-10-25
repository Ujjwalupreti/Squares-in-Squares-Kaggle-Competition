"""Search objective and optional overlap penalty.

The primary objective is to minimize L (container side length).
During search, infeasible intermediate states may be allowed using:
    J = L + lambda * P
where P penalizes overlapping pairs.
"""

from __future__ import annotations

import numpy as np

from ..geometry.bounds import container_side_length
from ..geometry.sat import compute_overlap_penalty


def compute_objective(
    squares: np.ndarray,
    overlap_lambda: float = 1000.0,
) -> tuple[float, float, float]:
    """Compute the search objective.

    Args:
        squares: array of shape (n, 3).
        overlap_lambda: weight for overlap penalty.

    Returns:
        (J, L, P) where J = L + lambda * P,
        L = container side length, P = overlap penalty.
    """
    L = container_side_length(squares)
    P = compute_overlap_penalty(squares)
    J = L + overlap_lambda * P
    return J, L, P
