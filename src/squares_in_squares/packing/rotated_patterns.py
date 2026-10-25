"""Rotated initial candidate patterns.

Some packings benefit from rotating squares (typically 45°) which
reduces the effective width in certain configurations.
"""

from __future__ import annotations

import math

import numpy as np

from ..puzzle import validate_n


def rotated_grid_packing(n: int, angle: float = math.pi / 4) -> np.ndarray:
    """Generate a grid packing with all squares rotated by a fixed angle.

    Spacing is increased to account for the rotated square extent:
    spacing = |cos(angle)| + |sin(angle)| (the diagonal extent).

    Args:
        n: number of unit squares to pack.
        angle: rotation angle in radians (default: π/4 = 45°).

    Returns:
        Array of shape (n, 3) with columns [x, y, angle].
    """
    validate_n(n)
    cols = math.ceil(math.sqrt(n))

    # Spacing must account for the full extent of a rotated square
    extent = abs(math.cos(angle)) + abs(math.sin(angle))

    squares = np.zeros((n, 3), dtype=np.float64)
    idx = 0
    row = 0
    while idx < n:
        for col in range(cols):
            if idx >= n:
                break
            squares[idx, 0] = col * extent + extent / 2
            squares[idx, 1] = row * extent + extent / 2
            squares[idx, 2] = angle
            idx += 1
        row += 1

    return squares


def corner_center_rotated_packing(n: int) -> np.ndarray | None:
    """Generate specialized rotated candidate packing patterns.

    For n = 5: 4 corner squares unrotated, 1 center square rotated at 45°.
    Achieves L = 2 + 1/sqrt(2) ≈ 2.7071 (vs grid L = 3.0), reducing
    the score from 0.3416 to 0.2107.

    Args:
        n: puzzle size.

    Returns:
        Array of shape (n, 3) or None if no specialized pattern for n.
    """
    if n == 5:
        L = 2.0 + 1.0 / math.sqrt(2.0)
        sq = np.zeros((5, 3), dtype=np.float64)
        sq[0] = [0.5, 0.5, 0.0]
        sq[1] = [L - 0.5, 0.5, 0.0]
        sq[2] = [0.5, L - 0.5, 0.0]
        sq[3] = [L - 0.5, L - 0.5, 0.0]
        sq[4] = [L / 2.0, L / 2.0, math.pi / 4.0]
        return sq
    return None
