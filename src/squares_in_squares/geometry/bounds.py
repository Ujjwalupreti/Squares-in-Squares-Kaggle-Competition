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


def batch_container_side_lengths(packings: dict[int, np.ndarray] | list[np.ndarray]) -> dict[int, float] | list[float]:
    """Compute container side lengths for a batch of packings.

    Args:
        packings: mapping of puzzle id to packing array, or list of packing arrays.

    Returns:
        Mapping or list of container side lengths corresponding to input.
    """
    if isinstance(packings, dict):
        return {k: container_side_length(v) for k, v in packings.items()}
    return [container_side_length(p) for p in packings]


def compute_minimum_separation(squares: np.ndarray) -> float:
    """Compute the minimum pairwise separation (clearance) across all squares in a packing.

    Uses the Separating Axis Theorem (SAT). For each pair of unit squares, the clearance
    is defined as the maximum separation distance over the 4 candidate normal axes.
    - Clearance > 0: pair is strictly disjoint with a positive buffer.
    - Clearance == 0: pair is in exact mathematical contact.
    - Clearance < 0: pair penetrates/overlaps by at least |clearance|.

    Args:
        squares: array of shape (n, 3) with [x, y, angle] in radians.

    Returns:
        Minimum clearance across all pairs in the packing, or +inf if n <= 1.
    """
    n = len(squares)
    if n <= 1:
        return float("inf")

    c = np.cos(squares[:, 2])
    s = np.sin(squares[:, 2])
    ux = np.column_stack([c, s])
    uy = np.column_stack([-s, c])
    centers = squares[:, :2]

    min_overall_sep = float("inf")

    for i in range(n):
        for j in range(i + 1, n):
            d = centers[j] - centers[i]
            # Fast bounding rejection
            if abs(d[0]) > 1.45 and abs(d[1]) > 1.45:
                continue

            axes = (ux[i], uy[i], ux[j], uy[j])
            max_axis_gap = -float("inf")
            for ax in axes:
                r_i = 0.5 * (abs(float(np.dot(ux[i], ax))) + abs(float(np.dot(uy[i], ax))))
                r_j = 0.5 * (abs(float(np.dot(ux[j], ax))) + abs(float(np.dot(uy[j], ax))))
                dist_proj = abs(float(np.dot(d, ax)))
                gap = dist_proj - (r_i + r_j)
                if gap > max_axis_gap:
                    max_axis_gap = gap

            if max_axis_gap < min_overall_sep:
                min_overall_sep = max_axis_gap

    return min_overall_sep
