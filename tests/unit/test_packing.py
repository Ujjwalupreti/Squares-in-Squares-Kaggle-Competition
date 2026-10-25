"""Unit tests for packing strategies."""

from __future__ import annotations

import math
import numpy as np
import pytest

from squares_in_squares.packing.grid import grid_packing
from squares_in_squares.packing.staggered import staggered_packing
from squares_in_squares.packing.rotated_patterns import rotated_grid_packing
from squares_in_squares.validation.packing_validator import validate_packing_geometry
from squares_in_squares.geometry.sat import packing_has_overlap


class TestPackingStrategies:
    """Test suite for initial candidate packing generators."""

    @pytest.mark.parametrize("n", [1, 2, 4, 7, 9, 16, 25, 50, 100])
    def test_grid_packing_is_valid(self, n: int):
        squares = grid_packing(n)
        assert squares.shape == (n, 3)
        # All angles must be zero
        np.testing.assert_allclose(squares[:, 2], 0.0)
        vr = validate_packing_geometry(squares, n)
        assert vr.valid, f"Grid failed for n={n}: {vr.errors}"

    @pytest.mark.parametrize("n", [1, 2, 4, 6, 9, 12, 16])
    def test_staggered_packing_is_valid(self, n: int):
        squares = staggered_packing(n)
        assert squares.shape == (n, 3)
        vr = validate_packing_geometry(squares, n)
        assert vr.valid, f"Staggered failed for n={n}: {vr.errors}"

    @pytest.mark.parametrize("n", [1, 4, 9, 16])
    def test_rotated_grid_packing_is_valid(self, n: int):
        squares = rotated_grid_packing(n, angle=math.pi / 4)
        assert squares.shape == (n, 3)
        # Angles must be pi/4
        np.testing.assert_allclose(squares[:, 2], math.pi / 4)
        has_overlap, pairs = packing_has_overlap(squares)
        assert not has_overlap, f"Rotated grid had overlaps: {pairs}"

    def test_invalid_n_raises(self):
        with pytest.raises(ValueError):
            grid_packing(0)
        with pytest.raises(ValueError):
            grid_packing(1001)
        with pytest.raises(ValueError):
            staggered_packing(-5)
