"""Unit tests for master multi-portfolio merge and hardening pipeline."""

import math
import numpy as np
import pytest

from squares_in_squares.geometry.bounds import container_side_length, half_extents
from squares_in_squares.geometry.sat import packing_has_overlap
from squares_in_squares.geometry.transforms import canonicalize_packing, dilate_packing


class TestMasterMergePrimitives:
    """Test geometry canonicalization and dilation primitives."""

    def test_canonicalize_packing_origin(self):
        """Packing extents must be anchored exactly at (0, 0)."""
        squares = np.array([
            [10.5, 20.5, 0.0],
            [11.5, 20.5, 0.0],
            [10.5, 21.5, 0.0],
            [11.5, 21.5, 0.0],
        ], dtype=float)

        canon = canonicalize_packing(squares)
        h = half_extents(canon[:, 2])
        min_x = np.min(canon[:, 0] - h)
        min_y = np.min(canon[:, 1] - h)
        assert abs(min_x) < 1e-12
        assert abs(min_y) < 1e-12
        assert abs(container_side_length(canon) - 2.0) < 1e-12

    def test_canonicalize_packing_angles_modulo(self):
        """Angles should be mapped into [0, pi/2)."""
        squares = np.array([
            [1.0, 1.0, math.pi],
            [2.0, 1.0, 2.5 * math.pi],
        ], dtype=float)
        canon = canonicalize_packing(squares)
        assert np.all(canon[:, 2] >= 0.0)
        assert np.all(canon[:, 2] < math.pi / 2.0 + 1e-12)

    def test_dilate_packing_eliminates_exact_contact(self):
        """Touching squares should obtain strictly positive clearance upon dilation."""
        squares = np.array([
            [0.5, 0.5, 0.0],
            [1.5, 0.5, 0.0],
        ], dtype=float)

        dilated = dilate_packing(squares, dilation_factor=1e-6)
        has_ov, _ = packing_has_overlap(dilated, tolerance=0.0)
        assert not has_ov
        gap = (dilated[1, 0] - 0.5) - (dilated[0, 0] + 0.5)
        assert gap > 0.0
