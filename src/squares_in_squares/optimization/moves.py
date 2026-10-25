"""Move operators for optimization.

Move families:
1. Small translation of one square.
2. Rotation of one square.
3. Combined translation and rotation.
4. Translation of a group of nearby squares.
5. Boundary-focused movement (move the square defining the largest extent).
"""

from __future__ import annotations

import numpy as np

from ..geometry.bounds import half_extents


def translate_one(
    squares: np.ndarray,
    idx: int,
    dx: float,
    dy: float,
) -> np.ndarray:
    """Move one square by (dx, dy).

    Args:
        squares: packing array (n, 3).
        idx: index of the square to move.
        dx, dy: translation amounts.

    Returns:
        New packing array with the move applied.
    """
    result = squares.copy()
    result[idx, 0] += dx
    result[idx, 1] += dy
    return result


def rotate_one(
    squares: np.ndarray,
    idx: int,
    dangle: float,
) -> np.ndarray:
    """Rotate one square by dangle radians.

    Args:
        squares: packing array (n, 3).
        idx: index of the square to rotate.
        dangle: rotation increment in radians.

    Returns:
        New packing array with the rotation applied.
    """
    result = squares.copy()
    result[idx, 2] += dangle
    return result


def translate_rotate_one(
    squares: np.ndarray,
    idx: int,
    dx: float,
    dy: float,
    dangle: float,
) -> np.ndarray:
    """Translate and rotate one square simultaneously.

    Args:
        squares: packing array (n, 3).
        idx: square index.
        dx, dy: translation.
        dangle: rotation.

    Returns:
        New packing array.
    """
    result = squares.copy()
    result[idx, 0] += dx
    result[idx, 1] += dy
    result[idx, 2] += dangle
    return result


def translate_group(
    squares: np.ndarray,
    indices: list[int],
    dx: float,
    dy: float,
) -> np.ndarray:
    """Translate a group of squares by the same amount.

    Args:
        squares: packing array (n, 3).
        indices: indices of squares to move.
        dx, dy: translation amounts.

    Returns:
        New packing array.
    """
    result = squares.copy()
    for idx in indices:
        result[idx, 0] += dx
        result[idx, 1] += dy
    return result


def find_boundary_square(squares: np.ndarray) -> int:
    """Find the square that most constrains the container size.

    Identifies the square whose removal would most reduce the container
    side length, by finding which square defines the current extremum.

    Args:
        squares: packing array (n, 3).

    Returns:
        Index of the boundary-defining square.
    """
    x = squares[:, 0]
    y = squares[:, 1]
    h = half_extents(squares[:, 2])

    # Find which square defines each extremum
    xmin_idx = int(np.argmin(x - h))
    xmax_idx = int(np.argmax(x + h))
    ymin_idx = int(np.argmin(y - h))
    ymax_idx = int(np.argmax(y + h))

    # The boundary square is one of these four
    # Return the one with the largest contribution
    xmin_val = float(x[xmin_idx] - h[xmin_idx])
    xmax_val = float(x[xmax_idx] + h[xmax_idx])
    ymin_val = float(y[ymin_idx] - h[ymin_idx])
    ymax_val = float(y[ymax_idx] + h[ymax_idx])

    x_span = xmax_val - xmin_val
    y_span = ymax_val - ymin_val

    if x_span >= y_span:
        # Width is the constraint; move one of the x-extreme squares
        return xmax_idx  # try to reduce the max
    else:
        return ymax_idx


def random_move(
    squares: np.ndarray,
    rng: np.random.Generator,
    translate_step: float = 0.1,
    rotate_step: float = 0.1,
    boundary_prob: float = 0.2,
) -> tuple[np.ndarray, str]:
    """Apply a random move to the packing.

    With probability boundary_prob, moves a boundary square.
    Otherwise, picks a random square and applies a random
    combination of translation and rotation.

    Args:
        squares: packing array (n, 3).
        rng: random number generator.
        translate_step: maximum translation per axis.
        rotate_step: maximum rotation.
        boundary_prob: probability of targeting a boundary square.

    Returns:
        (new_squares, move_name) with move applied and family name.
    """
    n = squares.shape[0]

    # Choose target square
    is_boundary = rng.random() < boundary_prob
    if is_boundary:
        idx = find_boundary_square(squares)
        prefix = "boundary_"
    else:
        idx = int(rng.integers(0, n))
        prefix = ""

    # Choose move type
    move_type = int(rng.integers(0, 3))

    if move_type == 0:
        # Translation only
        dx = float(rng.uniform(-translate_step, translate_step))
        dy = float(rng.uniform(-translate_step, translate_step))
        return translate_one(squares, idx, dx, dy), f"{prefix}translation"
    elif move_type == 1:
        # Rotation only
        dangle = float(rng.uniform(-rotate_step, rotate_step))
        return rotate_one(squares, idx, dangle), f"{prefix}rotation"
    else:
        # Combined
        dx = float(rng.uniform(-translate_step, translate_step))
        dy = float(rng.uniform(-translate_step, translate_step))
        dangle = float(rng.uniform(-rotate_step, rotate_step))
        return translate_rotate_one(squares, idx, dx, dy, dangle), f"{prefix}combined"
