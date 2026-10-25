"""Unit tests for objective function and overlap penalty."""

from __future__ import annotations

import math
import numpy as np
import pytest

from squares_in_squares.optimization.objective import compute_objective
from squares_in_squares.geometry.sat import compute_overlap_penalty
from squares_in_squares.geometry.bounds import container_side_length
from squares_in_squares.packing.grid import grid_packing


class TestObjective:
    """Test suite for search objective calculation."""

    def test_grid_has_zero_penalty(self):
        squares = grid_packing(9)
        P = compute_overlap_penalty(squares)
        assert P == 0.0

        J, L, P_ret = compute_objective(squares, overlap_lambda=1000.0)
        assert P_ret == 0.0
        assert J == pytest.approx(L)

    def test_overlapping_has_positive_penalty(self):
        # Two squares at exact same position
        squares = np.array([
            [0.5, 0.5, 0.0],
            [0.5, 0.5, 0.0],
        ])
        P = compute_overlap_penalty(squares)
        assert P > 0.0

        J, L, P_ret = compute_objective(squares, overlap_lambda=100.0)
        assert J == pytest.approx(L + 100.0 * P)

    def test_larger_overlap_increases_penalty(self):
        # Small overlap: distance = 0.95 (penetration ~ 0.05)
        sq_small = np.array([
            [0.0, 0.0, 0.0],
            [0.95, 0.0, 0.0],
        ])
        # Large overlap: distance = 0.5 (penetration ~ 0.5)
        sq_large = np.array([
            [0.0, 0.0, 0.0],
            [0.5, 0.0, 0.0],
        ])
        p_small = compute_overlap_penalty(sq_small)
        p_large = compute_overlap_penalty(sq_large)
        assert p_large > p_small
