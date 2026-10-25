"""Spatial index for broad-phase collision candidate filtering.

Uses an axis-aligned bounding box (AABB) grid to quickly identify
square pairs that might overlap, avoiding O(n²) SAT checks for
widely separated squares.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Set

import numpy as np

from .bounds import half_extents
from .sat import squares_overlap, DEFAULT_SAT_TOLERANCE


class SpatialGrid:
    """Grid-based spatial index for broad-phase collision filtering.

    Divides the plane into cells of a given size. Each square is
    inserted into all cells its AABB overlaps. Potential collisions
    are pairs of squares sharing a cell.
    """

    def __init__(self, cell_size: float = 1.5):
        """Initialize the spatial grid.

        Args:
            cell_size: side length of each grid cell. Should be >= 1
                (the unit square side length) to ensure correctness.
        """
        self.cell_size = cell_size
        self._cells: dict[tuple[int, int], list[int]] = defaultdict(list)
        self._squares: np.ndarray | None = None

    def build(self, squares: np.ndarray) -> None:
        """Build the spatial index from a packing.

        Args:
            squares: array of shape (n, 3) with columns [x, y, angle].
        """
        self._cells.clear()
        self._squares = squares
        n = squares.shape[0]
        h = half_extents(squares[:, 2])

        for i in range(n):
            x, y = squares[i, 0], squares[i, 1]
            hi = h[i]

            # AABB of square i
            x_min = x - hi
            x_max = x + hi
            y_min = y - hi
            y_max = y + hi

            # Cell range
            cx_min = int(np.floor(x_min / self.cell_size))
            cx_max = int(np.floor(x_max / self.cell_size))
            cy_min = int(np.floor(y_min / self.cell_size))
            cy_max = int(np.floor(y_max / self.cell_size))

            for cx in range(cx_min, cx_max + 1):
                for cy in range(cy_min, cy_max + 1):
                    self._cells[(cx, cy)].append(i)

    def candidate_pairs(self) -> Set[tuple[int, int]]:
        """Return all pairs of squares that share at least one grid cell.

        These are potential collision candidates that need SAT testing.

        Returns:
            Set of (i, j) pairs with i < j.
        """
        pairs: Set[tuple[int, int]] = set()
        for cell_indices in self._cells.values():
            for a_idx in range(len(cell_indices)):
                for b_idx in range(a_idx + 1, len(cell_indices)):
                    i, j = cell_indices[a_idx], cell_indices[b_idx]
                    if i > j:
                        i, j = j, i
                    pairs.add((i, j))
        return pairs

    def find_overlaps(
        self,
        tolerance: float = DEFAULT_SAT_TOLERANCE,
    ) -> list[tuple[int, int]]:
        """Find all overlapping pairs using broad+narrow phase.

        Args:
            tolerance: SAT tolerance for narrow-phase test.

        Returns:
            List of (i, j) overlapping pairs.
        """
        if self._squares is None:
            raise RuntimeError("Call build() before find_overlaps()")

        overlapping = []
        for i, j in self.candidate_pairs():
            si, sj = self._squares[i], self._squares[j]
            if squares_overlap(
                si[0], si[1], si[2],
                sj[0], sj[1], sj[2],
                tolerance=tolerance,
            ):
                overlapping.append((i, j))
        return overlapping
