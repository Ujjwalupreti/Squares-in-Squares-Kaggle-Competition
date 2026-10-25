"""Independent packing validation.

This validator is logically separate from the optimization objective.
It does NOT trust:
- An optimizer's cached collision result.
- A low overlap penalty.
- A previous validation result.
- A stored score without recomputation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..geometry.square import validate_packing
from ..geometry.bounds import container_side_length, container_side_length_from_corners
from ..geometry.sat import packing_has_overlap, DEFAULT_SAT_TOLERANCE
from ..geometry.spatial_index import SpatialGrid
from .score import puzzle_score


@dataclass
class ValidationResult:
    """Structured result from packing validation."""
    n: int
    valid: bool
    container_length: float = 0.0
    score: float = float('inf')
    errors: list[str] = field(default_factory=list)
    overlapping_pairs: list[tuple[int, int]] = field(default_factory=list)


def validate_packing_geometry(
    squares: np.ndarray,
    n: int,
    tolerance: float = DEFAULT_SAT_TOLERANCE,
    use_spatial_index: bool = True,
) -> ValidationResult:
    """Independently validate a complete packing.

    Checks:
    1. Correct number of squares.
    2. All coordinates and angles are finite.
    3. No pairwise interior overlaps (via SAT).
    4. Container bounds recomputed from full packing.
    5. Score recomputed independently.

    Args:
        squares: array of shape (n, 3).
        n: expected puzzle size.
        tolerance: SAT tolerance.
        use_spatial_index: if True and n > 50, use spatial grid for broad-phase.

    Returns:
        ValidationResult with detailed error information.
    """
    result = ValidationResult(n=n, valid=False)

    # 1. Shape and finiteness
    try:
        validate_packing(squares, n)
    except (TypeError, ValueError) as e:
        result.errors.append(f"Packing structure error: {e}")
        return result

    # 2. Check for overlaps
    if use_spatial_index and n > 50:
        # Use spatial index for large packings
        grid = SpatialGrid(cell_size=1.5)
        grid.build(squares)
        overlapping = grid.find_overlaps(tolerance=tolerance)
    else:
        # Exhaustive pairwise check for small packings
        _, overlapping = packing_has_overlap(squares, tolerance=tolerance)

    if overlapping:
        result.overlapping_pairs = overlapping
        result.errors.append(
            f"Found {len(overlapping)} overlapping pair(s): "
            f"{overlapping[:5]}{'...' if len(overlapping) > 5 else ''}"
        )
        return result

    # 3. Compute container bounds
    L = container_side_length(squares)

    # 4. Verify against corner-based calculation
    L_corners = container_side_length_from_corners(squares)
    if abs(L - L_corners) > 1e-10:
        result.errors.append(
            f"Container length mismatch: half-extent={L:.15f}, "
            f"corners={L_corners:.15f}, diff={abs(L - L_corners):.2e}"
        )
        return result

    # 5. Compute score
    result.container_length = L
    result.score = puzzle_score(n, L)
    result.valid = True

    return result
