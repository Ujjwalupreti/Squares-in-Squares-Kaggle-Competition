"""Oriented square axes and corner calculations.

For a unit square centered at (x, y) with rotation angle theta:
  e1 = (cos(theta), sin(theta))     — local x-axis
  e2 = (-sin(theta), cos(theta))    — local y-axis

The four corners are: center + 0.5 * (a * e1 + b * e2) for a,b in {-1,+1}.
"""

from __future__ import annotations

import numpy as np


def local_axes(angle: float) -> tuple[np.ndarray, np.ndarray]:
    """Compute the two local axes of a unit square at the given rotation.

    Args:
        angle: rotation in radians.

    Returns:
        (e1, e2) where e1 = (cos(theta), sin(theta)),
                       e2 = (-sin(theta), cos(theta)).
    """
    c = np.cos(angle)
    s = np.sin(angle)
    e1 = np.array([c, s], dtype=np.float64)
    e2 = np.array([-s, c], dtype=np.float64)
    return e1, e2


def corners(x: float, y: float, angle: float) -> np.ndarray:
    """Compute the four corners of a unit square.

    Args:
        x, y: center coordinates.
        angle: rotation in radians.

    Returns:
        Array of shape (4, 2) with corner coordinates.
        Order: (+,+), (+,-), (-,+), (-,-) in terms of (a,b) signs.
    """
    e1, e2 = local_axes(angle)
    center = np.array([x, y], dtype=np.float64)
    result = np.empty((4, 2), dtype=np.float64)
    idx = 0
    for a in (1.0, -1.0):
        for b in (1.0, -1.0):
            result[idx] = center + 0.5 * (a * e1 + b * e2)
            idx += 1
    return result


def corners_vectorized(squares: np.ndarray) -> np.ndarray:
    """Compute corners for all squares in a packing.

    Args:
        squares: array of shape (n, 3) with columns [x, y, angle].

    Returns:
        Array of shape (n, 4, 2) with corner coordinates for each square.
    """
    n = squares.shape[0]
    x, y, angles = squares[:, 0], squares[:, 1], squares[:, 2]

    c = np.cos(angles)
    s = np.sin(angles)

    # e1 = (cos, sin), e2 = (-sin, cos), half-scaled
    e1x = 0.5 * c
    e1y = 0.5 * s
    e2x = -0.5 * s
    e2y = 0.5 * c

    result = np.empty((n, 4, 2), dtype=np.float64)
    idx = 0
    for a in (1.0, -1.0):
        for b in (1.0, -1.0):
            result[:, idx, 0] = x + a * e1x + b * e2x
            result[:, idx, 1] = y + a * e1y + b * e2y
            idx += 1
    return result


def canonicalize_packing(squares: np.ndarray) -> np.ndarray:
    """Canonicalize packing coordinates to lower-left origin (0, 0) and normalize angles.

    Args:
        squares: array of shape (n, 3) with columns [x, y, angle].

    Returns:
        Canonicalized packing anchored at (0, 0) with angles in [0, pi/2).
    """
    coords = squares.copy()
    c = np.abs(np.cos(coords[:, 2]))
    s = np.abs(np.sin(coords[:, 2]))
    h = 0.5 * (c + s)
    coords[:, 0] -= np.min(coords[:, 0] - h)
    coords[:, 1] -= np.min(coords[:, 1] - h)
    coords[:, 2] = np.mod(coords[:, 2], np.pi / 2.0)
    return coords


def dilate_packing(squares: np.ndarray, dilation_factor: float) -> np.ndarray:
    """Dilate square centers radially from centroid to ensure strict SAT non-overlap.

    Args:
        squares: array of shape (n, 3) with columns [x, y, angle].
        dilation_factor: relative radial expansion factor.

    Returns:
        Dilated and re-canonicalized packing array.
    """
    if dilation_factor <= 0:
        return canonicalize_packing(squares)
    coords = squares.copy()
    cx = float(np.mean(coords[:, 0]))
    cy = float(np.mean(coords[:, 1]))
    coords[:, 0] = cx + (coords[:, 0] - cx) * (1.0 + dilation_factor)
    coords[:, 1] = cy + (coords[:, 1] - cy) * (1.0 + dilation_factor)
    return canonicalize_packing(coords)

