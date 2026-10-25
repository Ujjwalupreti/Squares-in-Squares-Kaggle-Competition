"""Puzzle definition and size constraints."""

from __future__ import annotations

import math


MIN_N = 1
MAX_N = 1000
TOTAL_ROWS = sum(range(1, MAX_N + 1))  # 500500


def validate_n(n: int) -> None:
    """Validate puzzle size n.

    Raises:
        ValueError: if n is not an integer in [1, 1000].
    """
    if not isinstance(n, int):
        raise TypeError(f"Puzzle size n must be an integer, got {type(n).__name__}")
    if not (MIN_N <= n <= MAX_N):
        raise ValueError(f"Puzzle size n must be in [{MIN_N}, {MAX_N}], got {n}")


def expected_row_count(n_min: int = MIN_N, n_max: int = MAX_N) -> int:
    """Return expected total row count for a complete submission."""
    return sum(range(n_min, n_max + 1))


def grid_dimensions(n: int) -> tuple[int, int]:
    """Return (cols, rows) for a grid packing of n squares.

    cols = ceil(sqrt(n))
    rows = ceil(n / cols)
    """
    validate_n(n)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return cols, rows
