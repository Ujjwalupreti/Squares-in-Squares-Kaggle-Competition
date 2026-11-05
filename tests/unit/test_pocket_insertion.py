"""Unit tests for Pocket Insertion and Diagonal Stripe generators."""

import math
import numpy as np
import pytest

from squares_in_squares.optimization.pocket_insertion import (
    find_best_void_candidate,
    grow_packing_by_insertion,
)
from squares_in_squares.packing.diagonal_stripes import generate_diagonal_stripe_packing
from squares_in_squares.validation.packing_validator import validate_packing_geometry


class TestPocketInsertion:
    def test_find_best_void_candidate_in_sparse_box(self):
        """Should find void in sparse 3x3 container containing 3 squares."""
        sq = np.array([
            [0.5, 0.5, 0.0],
            [1.5, 0.5, 0.0],
            [0.5, 1.5, 0.0],
        ], dtype=np.float64)

        bx, by, bth, ovs = find_best_void_candidate(sq, target_L=3.0, grid_resolution=15)
        assert ovs == 0
        assert bx > 1.2
        assert by > 1.2

    def test_grow_packing_by_insertion_n4_to_n5(self):
        """Growing a 4-square packing to 5 squares produces valid geometry."""
        # 4 squares in 3x3 container
        sq4 = np.array([
            [0.5, 0.5, 0.0],
            [2.5, 0.5, 0.0],
            [0.5, 2.5, 0.0],
            [2.5, 2.5, 0.0],
        ], dtype=np.float64)

        new_sq, L_new, success = grow_packing_by_insertion(sq4, 5, grid_resolution=15)
        if success:
            assert new_sq is not None
            vr = validate_packing_geometry(new_sq, 5)
            assert vr.valid
            assert L_new < 3.0


class TestDiagonalStripes:
    def test_diagonal_stripe_generator_returns_valid_or_none(self):
        """Diagonal stripe generator should only return SAT-certified packings."""
        for n in [5, 10, 17]:
            sq, L, success = generate_diagonal_stripe_packing(n)
            if success:
                assert sq is not None
                vr = validate_packing_geometry(sq, n)
                assert vr.valid
                k = int(math.ceil(math.sqrt(n)))
                assert L < k

