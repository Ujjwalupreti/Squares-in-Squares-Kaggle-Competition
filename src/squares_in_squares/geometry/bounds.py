"""Axis-aligned bounds and container side length calculation.

For a unit square at angle theta, its axis-aligned half-extent is:
    h = (|cos(theta)| + |sin(theta)|) / 2

Container bounds are computed from all squares' (x ± h, y ± h) extents.
Container side length L = max(xmax - xmin, ymax - ymin).
"""

from __future__ import annotations

import numpy as np

from .transforms import corners_vectorized


def half_extents(angles: np.ndarray) -> np.ndarray:
    """Compute axis-aligned half-extents for unit squares at given angles.

    Args:
        angles: array of rotation angles in radians.

    Returns:
        Array of half-extents h = (|cos(theta)| + |sin(theta)|) / 2.
    """
    return (np.abs(np.cos(angles)) + np.abs(np.sin(angles))) / 2.0


def container_bounds(squares: np.ndarray) -> tuple[float, float, float, float]:
    """Compute the axis-aligned bounding box of a packing.

    Uses the half-extent formula for efficiency and correctness.

    Args:
        squares: array of shape (n, 3) with columns [x, y, angle].

    Returns:
        (xmin, xmax, ymin, ymax).
    """
    x = squares[:, 0]
    y = squares[:, 1]
    h = half_extents(squares[:, 2])

    xmin = float(np.min(x - h))
    xmax = float(np.max(x + h))
    ymin = float(np.min(y - h))
    ymax = float(np.max(y + h))

    return xmin, xmax, ymin, ymax


def container_side_length(squares: np.ndarray) -> float:
    """Compute the container side length L for a packing.

    L = max(xmax - xmin, ymax - ymin).

    Args:
        squares: array of shape (n, 3).

    Returns:
        Container side length.
    """
    xmin, xmax, ymin, ymax = container_bounds(squares)
    return max(xmax - xmin, ymax - ymin)


def container_side_length_from_corners(squares: np.ndarray) -> float:
    """Compute container side length using explicit corner calculations.

    This is an independent reference implementation for verification.
    Slower but directly computes from the actual corner coordinates.

    Args:
        squares: array of shape (n, 3).

    Returns:
        Container side length.
    """
    all_corners = corners_vectorized(squares)  # (n, 4, 2)
    all_x = all_corners[:, :, 0].ravel()
    all_y = all_corners[:, :, 1].ravel()

    xmin = float(np.min(all_x))
    xmax = float(np.max(all_x))
    ymin = float(np.min(all_y))
    ymax = float(np.max(all_y))

    return max(xmax - xmin, ymax - ymin)
