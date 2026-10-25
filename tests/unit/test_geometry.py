"""Comprehensive geometry tests for Phase 1.

Tests cover:
- Square representation and validation
- Corner calculations
- Container bounds
- SAT collision detection
- Spatial index
- Score calculation
"""

from __future__ import annotations

import math
import pytest
import numpy as np

from squares_in_squares.geometry.square import (
    validate_square, validate_packing, make_packing,
)
from squares_in_squares.geometry.transforms import (
    local_axes, corners, corners_vectorized,
)
from squares_in_squares.geometry.bounds import (
    half_extents, container_bounds, container_side_length,
    container_side_length_from_corners,
)
from squares_in_squares.geometry.sat import (
    squares_overlap, packing_has_overlap, DEFAULT_SAT_TOLERANCE,
)
from squares_in_squares.geometry.spatial_index import SpatialGrid
from squares_in_squares.validation.score import puzzle_score


# ==================== Square Validation ====================

class TestSquareValidation:
    """Tests for square input validation."""

    def test_valid_square(self):
        validate_square(0.5, 0.5, 0.0)
        validate_square(-100.0, 200.0, math.pi)
        validate_square(0, 0, 0)  # int should work

    def test_nan_x(self):
        with pytest.raises(ValueError, match="finite"):
            validate_square(float('nan'), 0.5, 0.0)

    def test_nan_y(self):
        with pytest.raises(ValueError, match="finite"):
            validate_square(0.5, float('nan'), 0.0)

    def test_nan_angle(self):
        with pytest.raises(ValueError, match="finite"):
            validate_square(0.5, 0.5, float('nan'))

    def test_inf_x(self):
        with pytest.raises(ValueError, match="finite"):
            validate_square(float('inf'), 0.5, 0.0)

    def test_neg_inf_y(self):
        with pytest.raises(ValueError, match="finite"):
            validate_square(0.5, float('-inf'), 0.0)

    def test_string_type(self):
        with pytest.raises(TypeError, match="numeric"):
            validate_square("abc", 0.5, 0.0)

    def test_none_type(self):
        with pytest.raises(TypeError, match="numeric"):
            validate_square(None, 0.5, 0.0)


class TestPackingValidation:
    """Tests for packing array validation."""

    def test_valid_packing(self):
        squares = np.array([[0.5, 0.5, 0.0]], dtype=np.float64)
        validate_packing(squares, 1)

    def test_wrong_count(self):
        squares = np.array([[0.5, 0.5, 0.0]], dtype=np.float64)
        with pytest.raises(ValueError, match="Expected 2"):
            validate_packing(squares, 2)

    def test_wrong_shape(self):
        squares = np.array([[0.5, 0.5]], dtype=np.float64)
        with pytest.raises(ValueError, match="shape"):
            validate_packing(squares, 1)

    def test_nan_in_packing(self):
        squares = np.array([[0.5, float('nan'), 0.0]], dtype=np.float64)
        with pytest.raises(ValueError, match="finite"):
            validate_packing(squares, 1)

    def test_not_array(self):
        with pytest.raises(TypeError, match="numpy array"):
            validate_packing([[0.5, 0.5, 0.0]], 1)


# ==================== Corner Calculations ====================

class TestCorners:
    """Tests for corner calculations."""

    def test_unit_square_at_origin(self):
        """Unrotated unit square centered at (0.5, 0.5)."""
        c = corners(0.5, 0.5, 0.0)
        assert c.shape == (4, 2)

        # Should have corners at (0,0), (0,1), (1,0), (1,1)
        expected_x = {0.0, 1.0}
        expected_y = {0.0, 1.0}
        actual_x = set(np.round(c[:, 0], 10))
        actual_y = set(np.round(c[:, 1], 10))
        assert actual_x == expected_x
        assert actual_y == expected_y

    def test_rotated_45_degrees(self):
        """Square rotated 45° should have corners along diagonals."""
        angle = math.pi / 4
        c = corners(0.0, 0.0, angle)
        half_diag = math.sqrt(2) / 2  # 0.5 * sqrt(2) ≈ 0.7071

        # Each corner should be at distance 0.5*sqrt(2) from center
        for i in range(4):
            dist = math.sqrt(c[i, 0]**2 + c[i, 1]**2)
            assert abs(dist - half_diag) < 1e-10

    def test_rotated_90_degrees(self):
        """Square rotated 90° should have same footprint as 0°."""
        c0 = corners(1.0, 1.0, 0.0)
        c90 = corners(1.0, 1.0, math.pi / 2)

        # Same set of corners (x and y swap)
        xs0 = set(np.round(c0[:, 0], 10))
        xs90 = set(np.round(c90[:, 0], 10))
        assert xs0 == xs90

    def test_vectorized_matches_scalar(self):
        """Vectorized corner computation matches scalar version."""
        squares = np.array([
            [0.5, 0.5, 0.0],
            [2.0, 3.0, math.pi / 6],
            [0.0, 0.0, math.pi / 4],
        ], dtype=np.float64)

        vec_corners = corners_vectorized(squares)
        for i in range(3):
            scalar_corners = corners(squares[i, 0], squares[i, 1], squares[i, 2])
            np.testing.assert_allclose(vec_corners[i], scalar_corners, atol=1e-12)


# ==================== Container Bounds ====================

class TestBounds:
    """Tests for container bounds calculation."""

    def test_single_unrotated_square(self):
        """One unrotated square at (0.5, 0.5)."""
        squares = np.array([[0.5, 0.5, 0.0]], dtype=np.float64)
        L = container_side_length(squares)
        assert abs(L - 1.0) < 1e-10

    def test_two_adjacent_squares(self):
        """Two unrotated squares side by side."""
        squares = np.array([
            [0.5, 0.5, 0.0],
            [1.5, 0.5, 0.0],
        ], dtype=np.float64)
        L = container_side_length(squares)
        assert abs(L - 2.0) < 1e-10

    def test_rotated_square_extent(self):
        """45° rotated square has larger extent than unrotated."""
        # Unrotated
        s0 = np.array([[0.5, 0.5, 0.0]], dtype=np.float64)
        L0 = container_side_length(s0)

        # 45° rotated
        s45 = np.array([[0.5, 0.5, math.pi / 4]], dtype=np.float64)
        L45 = container_side_length(s45)

        assert L45 > L0
        expected_45 = math.sqrt(2)  # diagonal of unit square
        assert abs(L45 - expected_45) < 1e-10

    def test_half_extent_formula(self):
        """Verify h = (|cos(θ)| + |sin(θ)|) / 2."""
        angles = np.array([0.0, math.pi / 4, math.pi / 2, math.pi / 6])
        h = half_extents(angles)

        for i, angle in enumerate(angles):
            expected = (abs(math.cos(angle)) + abs(math.sin(angle))) / 2
            assert abs(h[i] - expected) < 1e-15

    def test_bounds_match_corners(self):
        """Half-extent bounds must agree with corner-based calculation."""
        squares = np.array([
            [1.0, 2.0, 0.3],
            [3.0, 1.0, 0.7],
            [2.0, 3.0, 1.2],
        ], dtype=np.float64)

        L_formula = container_side_length(squares)
        L_corners = container_side_length_from_corners(squares)
        assert abs(L_formula - L_corners) < 1e-10

    def test_bounds_match_corners_many_angles(self):
        """Test bounds agreement for many random angles."""
        rng = np.random.default_rng(12345)
        for _ in range(100):
            n = rng.integers(1, 20)
            squares = np.column_stack([
                rng.uniform(-10, 10, n),
                rng.uniform(-10, 10, n),
                rng.uniform(0, 2 * math.pi, n),
            ])
            L_formula = container_side_length(squares)
            L_corners = container_side_length_from_corners(squares)
            assert abs(L_formula - L_corners) < 1e-10, \
                f"Mismatch: formula={L_formula}, corners={L_corners}"

    def test_large_coordinates(self):
        """Bounds work with large coordinate values."""
        squares = np.array([
            [1e6, 1e6, 0.0],
            [1e6 + 1, 1e6, 0.0],
        ], dtype=np.float64)
        L = container_side_length(squares)
        assert abs(L - 2.0) < 1e-6

    def test_small_coordinates(self):
        """Bounds work with small coordinate values."""
        squares = np.array([
            [1e-8, 1e-8, 0.0],
        ], dtype=np.float64)
        L = container_side_length(squares)
        assert abs(L - 1.0) < 1e-10


# ==================== SAT Collision Detection ====================

class TestSAT:
    """Tests for Separating Axis Theorem collision detection."""

    def test_separated_squares(self):
        """Two clearly separated squares should not overlap."""
        assert not squares_overlap(0.5, 0.5, 0.0, 5.5, 5.5, 0.0)

    def test_touching_squares_x(self):
        """Two squares touching along x-axis (contact is allowed)."""
        # Centers at 0.5 and 1.5, each has half-width 0.5
        # They touch at x=1.0
        assert not squares_overlap(0.5, 0.5, 0.0, 1.5, 0.5, 0.0)

    def test_touching_squares_y(self):
        """Two squares touching along y-axis."""
        assert not squares_overlap(0.5, 0.5, 0.0, 0.5, 1.5, 0.0)

    def test_overlapping_squares(self):
        """Two clearly overlapping squares."""
        # Centers only 0.5 apart, each has half-width 0.5
        assert squares_overlap(0.5, 0.5, 0.0, 1.0, 0.5, 0.0)

    def test_identical_squares(self):
        """Two identical squares at the same position."""
        assert squares_overlap(0.5, 0.5, 0.0, 0.5, 0.5, 0.0)

    def test_diagonal_separation(self):
        """Squares separated diagonally."""
        # Just far enough apart diagonally
        assert not squares_overlap(0.5, 0.5, 0.0, 3.5, 3.5, 0.0)

    def test_diagonal_overlap(self):
        """Squares close along the diagonal but actually not overlapping."""
        # At (0.5,0.5) and (1.5,1.5), these touch at corner (1,1)
        assert not squares_overlap(0.5, 0.5, 0.0, 1.5, 1.5, 0.0)

    def test_slight_overlap(self):
        """Squares slightly overlapping."""
        # Centers at distance 0.99 apart (each half-width 0.5)
        assert squares_overlap(0.5, 0.5, 0.0, 1.49, 0.5, 0.0)

    def test_rotated_separated(self):
        """Two rotated squares that are separated."""
        assert not squares_overlap(0.0, 0.0, 0.3, 3.0, 0.0, 0.7)

    def test_rotated_overlapping(self):
        """Two rotated squares that overlap."""
        assert squares_overlap(0.0, 0.0, 0.3, 0.3, 0.0, 0.7)

    def test_one_rotated_45_touching(self):
        """One square rotated 45° touching an unrotated square."""
        # Rotated square at origin: half-extent = sqrt(2)/2 ≈ 0.7071
        # Unrotated square at x = sqrt(2)/2 + 0.5 = 1.2071
        dist = math.sqrt(2) / 2 + 0.5
        assert not squares_overlap(0.0, 0.0, math.pi / 4, dist, 0.0, 0.0)

    def test_one_rotated_45_overlapping(self):
        """One square rotated 45° overlapping an unrotated square."""
        dist = math.sqrt(2) / 2 + 0.5 - 0.1  # slightly too close
        assert squares_overlap(0.0, 0.0, math.pi / 4, dist, 0.0, 0.0)

    def test_corner_contact(self):
        """Corner contact should be allowed."""
        # Two unrotated squares touching at corner (1,1)
        assert not squares_overlap(0.5, 0.5, 0.0, 1.5, 1.5, 0.0)

    def test_nearly_parallel_edges(self):
        """Squares with nearly parallel edges and small gap."""
        # Very small rotation, side by side
        eps = 1e-12
        assert not squares_overlap(0.5, 0.5, eps, 1.5, 0.5, -eps)

    def test_packing_no_overlap(self):
        """Grid packing should have no overlaps."""
        squares = np.array([
            [0.5, 0.5, 0.0],
            [1.5, 0.5, 0.0],
            [0.5, 1.5, 0.0],
            [1.5, 1.5, 0.0],
        ], dtype=np.float64)
        has_overlap, pairs = packing_has_overlap(squares)
        assert not has_overlap
        assert pairs == []

    def test_packing_with_overlap(self):
        """Packing with one overlapping pair."""
        squares = np.array([
            [0.5, 0.5, 0.0],
            [1.0, 0.5, 0.0],  # overlaps with first
            [0.5, 5.5, 0.0],  # far away
        ], dtype=np.float64)
        has_overlap, pairs = packing_has_overlap(squares)
        assert has_overlap
        assert (0, 1) in pairs


# ==================== Spatial Index ====================

class TestSpatialIndex:
    """Tests for spatial index correctness."""

    def test_grid_no_overlaps(self):
        """Spatial index finds no overlaps in a grid."""
        squares = np.array([
            [0.5, 0.5, 0.0],
            [1.5, 0.5, 0.0],
            [0.5, 1.5, 0.0],
            [1.5, 1.5, 0.0],
        ], dtype=np.float64)
        grid = SpatialGrid(cell_size=1.5)
        grid.build(squares)
        overlaps = grid.find_overlaps()
        assert overlaps == []

    def test_finds_overlap(self):
        """Spatial index finds actual overlaps."""
        squares = np.array([
            [0.5, 0.5, 0.0],
            [0.8, 0.5, 0.0],  # overlaps
            [5.0, 5.0, 0.0],  # far away
        ], dtype=np.float64)
        grid = SpatialGrid(cell_size=1.5)
        grid.build(squares)
        overlaps = grid.find_overlaps()
        assert len(overlaps) == 1
        assert (0, 1) in overlaps

    def test_spatial_matches_exhaustive(self):
        """Spatial index overlaps match exhaustive check for random packings."""
        rng = np.random.default_rng(42)
        for trial in range(20):
            n = rng.integers(5, 30)
            squares = np.column_stack([
                rng.uniform(0, 5, n),
                rng.uniform(0, 5, n),
                rng.uniform(0, math.pi / 2, n),
            ])

            # Exhaustive
            _, exhaustive_pairs = packing_has_overlap(squares)

            # Spatial index
            grid = SpatialGrid(cell_size=1.5)
            grid.build(squares)
            spatial_overlaps = grid.find_overlaps()

            # Spatial must find ALL overlaps (may have duplicates)
            exhaustive_set = set(exhaustive_pairs)
            spatial_set = set(spatial_overlaps)
            assert exhaustive_set == spatial_set, \
                f"Trial {trial}: exhaustive={exhaustive_set}, spatial={spatial_set}"


# ==================== Score Calculation ====================

class TestScore:
    """Tests for score calculation."""

    def test_n1_score(self):
        """Score for n=1, L=1 should be 0."""
        assert abs(puzzle_score(1, 1.0)) < 1e-15

    def test_n4_optimal(self):
        """Score for n=4 in a 2x2 grid: L=2, score=0."""
        assert abs(puzzle_score(4, 2.0)) < 1e-15

    def test_positive_score(self):
        """Container larger than sqrt(n) gives positive score."""
        score = puzzle_score(4, 3.0)
        assert score > 0
        assert abs(score - (3.0 / 2.0 - 1.0)) < 1e-15

    def test_invalid_n(self):
        with pytest.raises(ValueError):
            puzzle_score(0, 1.0)

    def test_invalid_L(self):
        with pytest.raises(ValueError):
            puzzle_score(1, -1.0)

    def test_inf_L(self):
        with pytest.raises(ValueError):
            puzzle_score(1, float('inf'))


# ==================== Randomized Property Tests ====================

class TestRandomizedGeometry:
    """Property-based tests using randomized inputs."""

    def test_container_always_at_least_1(self):
        """Container must be at least 1 for any single square."""
        rng = np.random.default_rng(999)
        for _ in range(200):
            angle = rng.uniform(0, 2 * math.pi)
            squares = np.array([[0.0, 0.0, angle]], dtype=np.float64)
            L = container_side_length(squares)
            assert L >= 1.0 - 1e-10

    def test_overlap_is_symmetric(self):
        """SAT overlap test should be symmetric."""
        rng = np.random.default_rng(77)
        for _ in range(200):
            x1, y1 = rng.uniform(-5, 5, 2)
            x2, y2 = rng.uniform(-5, 5, 2)
            a1, a2 = rng.uniform(0, math.pi, 2)
            assert squares_overlap(x1, y1, a1, x2, y2, a2) == \
                   squares_overlap(x2, y2, a2, x1, y1, a1)

    def test_identical_squares_always_overlap(self):
        """A square always overlaps with itself."""
        rng = np.random.default_rng(88)
        for _ in range(100):
            x, y = rng.uniform(-10, 10, 2)
            a = rng.uniform(0, 2 * math.pi)
            assert squares_overlap(x, y, a, x, y, a)

    def test_far_squares_never_overlap(self):
        """Squares more than sqrt(2) apart never overlap."""
        rng = np.random.default_rng(99)
        for _ in range(200):
            x1, y1 = rng.uniform(-10, 10, 2)
            a1, a2 = rng.uniform(0, 2 * math.pi, 2)
            # Place second square at distance > sqrt(2) + epsilon
            theta = rng.uniform(0, 2 * math.pi)
            dist = math.sqrt(2) + 0.01
            x2 = x1 + dist * math.cos(theta)
            y2 = y1 + dist * math.sin(theta)
            assert not squares_overlap(x1, y1, a1, x2, y2, a2)

    def test_bounds_formula_vs_corners(self):
        """Random test: half-extent formula and corners agree."""
        rng = np.random.default_rng(111)
        for _ in range(100):
            n = rng.integers(1, 50)
            squares = np.column_stack([
                rng.uniform(-100, 100, n),
                rng.uniform(-100, 100, n),
                rng.uniform(0, 2 * math.pi, n),
            ])
            L1 = container_side_length(squares)
            L2 = container_side_length_from_corners(squares)
            assert abs(L1 - L2) < 1e-9
