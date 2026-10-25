"""Alternative staggered initial layouts.

Staggered packing offsets alternating rows by 0.5 units,
which can allow for tighter packing especially with rotations.
"""

from __future__ import annotations

import numpy as np

from ..puzzle import validate_n


def staggered_packing(n: int) -> np.ndarray:
    """Generate a staggered grid packing.

    Alternating rows are offset by 0.5 units in x.
    Spacing is 1.0 unit (same as grid) for guaranteed feasibility.

    Args:
        n: number of unit squares to pack.

    Returns:
        Array of shape (n, 3) with columns [x, y, angle].
    """
    validate_n(n)
    import math
    cols = math.ceil(math.sqrt(n))

    squares = np.zeros((n, 3), dtype=np.float64)
    idx = 0
    row = 0
    while idx < n:
        offset = 0.25 if (row % 2 == 1) else 0.0
        for col in range(cols):
            if idx >= n:
                break
            squares[idx, 0] = col + 0.5 + offset
            squares[idx, 1] = row + 0.5
            idx += 1
        row += 1

    return squares
