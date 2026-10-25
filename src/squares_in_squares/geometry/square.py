"""Square representation and input validation.

Each square is represented as (x, y, angle) where:
- x, y: center coordinates (float)
- angle: rotation in radians (float)
- side length is always 1
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np


def validate_square(x: float, y: float, angle: float) -> None:
    """Validate a single square's parameters.

    Raises:
        ValueError: if any value is NaN or infinite.
        TypeError: if any value is not numeric.
    """
    for name, val in [("x", x), ("y", y), ("angle", angle)]:
        if not isinstance(val, (int, float, np.floating, np.integer)):
            raise TypeError(f"Square parameter '{name}' must be numeric, got {type(val).__name__}")
        if math.isnan(float(val)) or math.isinf(float(val)):
            raise ValueError(f"Square parameter '{name}' must be finite, got {val}")


def validate_packing(squares: np.ndarray, n: int) -> None:
    """Validate a packing array has shape (n, 3) with all finite values.

    Args:
        squares: array of shape (n, 3) with columns [x, y, angle].
        n: expected number of squares.

    Raises:
        ValueError: if shape is wrong or values are non-finite.
    """
    if not isinstance(squares, np.ndarray):
        raise TypeError(f"Packing must be a numpy array, got {type(squares).__name__}")
    if squares.ndim != 2 or squares.shape[1] != 3:
        raise ValueError(f"Packing must have shape (n, 3), got {squares.shape}")
    if squares.shape[0] != n:
        raise ValueError(f"Expected {n} squares, got {squares.shape[0]}")
    if not np.all(np.isfinite(squares)):
        raise ValueError("All square parameters must be finite (no NaN or inf)")


def make_packing(squares: Sequence[tuple[float, float, float]]) -> np.ndarray:
    """Create a packing array from a sequence of (x, y, angle) tuples."""
    arr = np.array(squares, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr.reshape(1, 3)
    return arr
