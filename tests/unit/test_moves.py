"""Unit tests for move operators."""

from __future__ import annotations

import math
import numpy as np
import pytest

from squares_in_squares.optimization.moves import (
    translate_one,
    rotate_one,
    translate_rotate_one,
    translate_group,
    find_boundary_square,
    random_move,
)
from squares_in_squares.packing.grid import grid_packing
from squares_in_squares.geometry.bounds import container_side_length


class TestMoves:
    """Test suite for individual move operators."""

    def test_translate_one(self):
        squares = grid_packing(4)
        orig = squares.copy()
        moved = translate_one(squares, 0, 0.5, -0.2)

        # Moved square is changed
        assert moved[0, 0] == pytest.approx(orig[0, 0] + 0.5)
        assert moved[0, 1] == pytest.approx(orig[0, 1] - 0.2)
        assert moved[0, 2] == pytest.approx(orig[0, 2])

        # Other squares unchanged
        np.testing.assert_allclose(moved[1:], orig[1:])

    def test_rotate_one(self):
        squares = grid_packing(4)
        orig = squares.copy()
        angle = math.pi / 6
        rotated = rotate_one(squares, 2, angle)

        # Rotated square angle changed, position unchanged
        assert rotated[2, 0] == pytest.approx(orig[2, 0])
        assert rotated[2, 1] == pytest.approx(orig[2, 1])
        assert rotated[2, 2] == pytest.approx(angle)

        # Other squares unchanged
        np.testing.assert_allclose(rotated[:2], orig[:2])
        np.testing.assert_allclose(rotated[3:], orig[3:])

    def test_translate_rotate_one(self):
        squares = grid_packing(4)
        orig = squares.copy()
        result = translate_rotate_one(squares, 1, 0.1, -0.1, 0.2)

        assert result[1, 0] == pytest.approx(orig[1, 0] + 0.1)
        assert result[1, 1] == pytest.approx(orig[1, 1] - 0.1)
        assert result[1, 2] == pytest.approx(orig[1, 2] + 0.2)

    def test_translate_group(self):
        squares = grid_packing(9)
        orig = squares.copy()
        indices = [0, 1, 2]
        result = translate_group(squares, indices, 1.0, 2.0)

        for idx in indices:
            assert result[idx, 0] == pytest.approx(orig[idx, 0] + 1.0)
            assert result[idx, 1] == pytest.approx(orig[idx, 1] + 2.0)

        for idx in range(3, 9):
            np.testing.assert_allclose(result[idx], orig[idx])

    def test_find_boundary_square(self):
        # A 2x2 grid: squares at (0.5, 0.5), (1.5, 0.5), (0.5, 1.5), (1.5, 1.5)
        squares = grid_packing(4)
        boundary_idx = find_boundary_square(squares)
        assert boundary_idx in [1, 2, 3]  # on boundary

        # If we push square 0 far out, it must become the boundary square
        squares[0, 0] = 100.0
        assert find_boundary_square(squares) == 0

    def test_random_move_respects_steps(self):
        rng = np.random.default_rng(123)
        squares = grid_packing(5)
        for _ in range(50):
            moved, move_name = random_move(squares, rng, translate_step=0.2, rotate_step=0.3)
            assert isinstance(move_name, str)
            diff = np.abs(moved - squares)
            assert np.max(diff[:, 0]) <= 0.2000001
            assert np.max(diff[:, 1]) <= 0.2000001
            assert np.max(diff[:, 2]) <= 0.3000001
