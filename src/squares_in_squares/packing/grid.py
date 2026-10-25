"""Guaranteed-feasible axis-aligned grid baseline.

For each n:
    cols = ceil(sqrt(n))
    rows = ceil(n / cols)

Place square centers at:
    x = col + 0.5
    y = row + 0.5
    angle = 0

This produces non-overlapping unit squares with 1-unit spacing.
"""

from __future__ import annotations

import numpy as np

from ..puzzle import validate_n, grid_dimensions


def grid_packing(n: int) -> np.ndarray:
    """Generate a guaranteed-feasible axis-aligned grid packing.

    Args:
        n: number of unit squares to pack.

    Returns:
        Array of shape (n, 3) with columns [x, y, angle].
        All angles are 0. Centers are at integer + 0.5 positions.
    """
    validate_n(n)
    cols, rows = grid_dimensions(n)

    squares = np.zeros((n, 3), dtype=np.float64)
    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= n:
                break
            squares[idx, 0] = col + 0.5  # x
            squares[idx, 1] = row + 0.5  # y
            # angle = 0 already set
            idx += 1

    return squares
