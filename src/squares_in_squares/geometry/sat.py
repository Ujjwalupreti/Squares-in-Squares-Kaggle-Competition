"""Separating Axis Theorem (SAT) for oriented unit square collision detection.

Two convex shapes do not overlap if and only if there exists a separating axis
on which their projections do not overlap. For two squares, the candidate axes
are the four edge normals (two per square, since opposite edges share normals).

TOLERANCE POLICY (documented per RULES.md §3):
    We use a tolerance of 1e-9 for the SAT overlap test. This means:
    - Two squares whose projection overlap on ALL axes is less than 1e-9
      are considered non-overlapping (touching/contact is allowed).
    - Two squares with projection overlap > 1e-9 on all axes are overlapping.

    This tolerance is chosen to be:
    - Large enough to handle floating-point rounding in cos/sin calculations
      (typically ~1e-15 to 1e-14 per operation, accumulated to ~1e-12 max).
    - Small enough that any visually or geometrically meaningful overlap
      (say, 1e-6 or larger) is always detected.
"""

from __future__ import annotations

import numpy as np

from .transforms import local_axes
from .bounds import half_extents


# Default tolerance for SAT separation test.
# Overlap less than this on any axis counts as separation.
DEFAULT_SAT_TOLERANCE: float = 1e-9


def _project_radius(axis: np.ndarray, e1: np.ndarray, e2: np.ndarray) -> float:
    """Compute the projection half-width of a unit square onto an axis.

    For a unit square with local axes e1, e2 (each of length 1),
    the half-side is 0.5, so:
        radius = 0.5 * |axis . e1| + 0.5 * |axis . e2|

    Args:
        axis: unit direction vector (2,).
        e1: first local axis of the square (2,).
        e2: second local axis of the square (2,).

    Returns:
        Projection half-width (radius).
    """
    return 0.5 * abs(np.dot(axis, e1)) + 0.5 * abs(np.dot(axis, e2))


def squares_overlap(
    x1: float, y1: float, angle1: float,
    x2: float, y2: float, angle2: float,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
) -> bool:
    """Test whether two unit squares have overlapping interiors.

    Uses the Separating Axis Theorem with four candidate axes
    (two from each square).

    Edge and corner contact is ALLOWED (not counted as overlap).

    Args:
        x1, y1, angle1: center and rotation of the first square.
        x2, y2, angle2: center and rotation of the second square.
        tolerance: numerical tolerance for separation.
            Overlap < tolerance on any axis → considered separated.

    Returns:
        True if the squares' interiors overlap, False otherwise.
    """
    e1a, e2a = local_axes(angle1)
    e1b, e2b = local_axes(angle2)

    # Vector from center1 to center2
    d = np.array([x2 - x1, y2 - y1], dtype=np.float64)

    # Test each of the four candidate separating axes
    for axis in (e1a, e2a, e1b, e2b):
        # Project the center-to-center distance onto this axis
        center_dist = abs(np.dot(d, axis))

        # Sum of projection radii
        r1 = _project_radius(axis, e1a, e2a)
        r2 = _project_radius(axis, e1b, e2b)

        # If projections are separated (with tolerance), no overlap
        if center_dist >= r1 + r2 - tolerance:
            return False

    # No separating axis found → interiors overlap
    return True


def packing_has_overlap(
    squares: np.ndarray,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
) -> tuple[bool, list[tuple[int, int]]]:
    """Check all pairs in a packing for interior overlap.

    Includes AABB broad-phase filtering before running narrow-phase SAT.

    Args:
        squares: array of shape (n, 3) with columns [x, y, angle].
        tolerance: SAT tolerance.

    Returns:
        (has_overlap, overlapping_pairs) where overlapping_pairs is a list
        of (i, j) index pairs that overlap.
    """
    n = squares.shape[0]
    overlapping = []
    h = half_extents(squares[:, 2])
    x = squares[:, 0]
    y = squares[:, 1]

    for i in range(n):
        xi, yi, hi = x[i], y[i], h[i]
        for j in range(i + 1, n):
            # AABB broad-phase test
            if abs(xi - x[j]) >= hi + h[j] - tolerance:
                continue
            if abs(yi - y[j]) >= hi + h[j] - tolerance:
                continue

            if squares_overlap(
                xi, yi, squares[i, 2],
                x[j], y[j], squares[j, 2],
                tolerance=tolerance,
            ):
                overlapping.append((i, j))
    return len(overlapping) > 0, overlapping


def compute_overlap_penalty(
    squares: np.ndarray,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
) -> float:
    """Compute a heuristic overlap penalty for optimization.

    Uses AABB broad-phase filtering and precomputed local axes for speed.
    For each pair of overlapping squares, compute the sum of
    penetration depths across all four SAT axes.

    NOTE: This is a search heuristic, NOT a proof of feasibility.

    Args:
        squares: array of shape (n, 3).
        tolerance: SAT tolerance.

    Returns:
        Total overlap penalty (0.0 if no overlaps).
    """
    n = squares.shape[0]
    total_penalty = 0.0
    h = half_extents(squares[:, 2])
    x = squares[:, 0]
    y = squares[:, 1]

    # Precompute local axes
    axes = [local_axes(squares[i, 2]) for i in range(n)]

    for i in range(n):
        e1a, e2a = axes[i]
        xi, yi, hi = x[i], y[i], h[i]

        for j in range(i + 1, n):
            # AABB broad-phase test
            if abs(xi - x[j]) >= hi + h[j] - tolerance:
                continue
            if abs(yi - y[j]) >= hi + h[j] - tolerance:
                continue

            e1b, e2b = axes[j]
            d = np.array([x[j] - xi, y[j] - yi], dtype=np.float64)

            # Check all axes; compute penetration
            min_penetration = float('inf')
            is_separated = False

            for axis in (e1a, e2a, e1b, e2b):
                center_dist = abs(np.dot(d, axis))
                r1 = _project_radius(axis, e1a, e2a)
                r2 = _project_radius(axis, e1b, e2b)
                gap = center_dist - (r1 + r2)

                if gap >= -tolerance:
                    is_separated = True
                    break
                penetration = -gap
                min_penetration = min(min_penetration, penetration)

            if not is_separated and min_penetration > 0:
                # Use squared penetration for smoother gradient
                total_penalty += min_penetration ** 2

    return total_penalty
