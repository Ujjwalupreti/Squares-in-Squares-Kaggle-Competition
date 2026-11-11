"""Unit tests for performance optimizations, clearance metrics, and audit summary."""

import math
import numpy as np
import pytest

from squares_in_squares.geometry.bounds import (
    container_side_length,
    batch_container_side_lengths,
    compute_minimum_separation,
)
from squares_in_squares.packing.grid import grid_packing
from squares_in_squares.validation.submission_validator import (
    audit_summary,
    SubmissionAuditResult,
)


class TestSeparationAndClearance:
    """Tests for pairwise minimum separation calculation."""

    def test_single_square_clearance(self):
        sq = np.array([[0.5, 0.5, 0.0]])
        sep = compute_minimum_separation(sq)
        assert math.isinf(sep) and sep > 0

    def test_touching_squares_zero_clearance(self):
        # Two unit squares touching at edge x=1.0
        sq = np.array([
            [0.5, 0.5, 0.0],
            [1.5, 0.5, 0.0],
        ])
        sep = compute_minimum_separation(sq)
        assert abs(sep) < 1e-12

    def test_separated_squares_positive_clearance(self):
        # Two unit squares separated by gap of 0.2 along x
        sq = np.array([
            [0.5, 0.5, 0.0],
            [1.7, 0.5, 0.0],
        ])
        sep = compute_minimum_separation(sq)
        assert abs(sep - 0.2) < 1e-10

    def test_overlapping_squares_negative_clearance(self):
        # Two unit squares penetrating by 0.1 along x
        sq = np.array([
            [0.5, 0.5, 0.0],
            [1.4, 0.5, 0.0],
        ])
        sep = compute_minimum_separation(sq)
        assert sep < -0.05

    def test_gobel_safeguard_positive_clearance(self):
        # N=5 with positive clearance epsilon = 1e-7
        L5 = 2.0 + 1.0 / math.sqrt(2.0) + 1e-7
        sq = np.array([
            [0.5, 0.5, 0.0],
            [L5 - 0.5, 0.5, 0.0],
            [0.5, L5 - 0.5, 0.0],
            [L5 - 0.5, L5 - 0.5, 0.0],
            [L5 / 2.0, L5 / 2.0, math.pi / 4.0],
        ])
        sep = compute_minimum_separation(sq)
        assert sep > 0.0, f"Expected positive separation for buffered Göbel, got {sep}"


class TestBatchContainerLengths:
    """Tests for batch container side length calculations."""

    def test_batch_dict(self):
        p1 = grid_packing(1)
        p4 = grid_packing(4)
        p9 = grid_packing(9)
        packings = {1: p1, 4: p4, 9: p9}
        res = batch_container_side_lengths(packings)
        assert isinstance(res, dict)
        assert abs(res[1] - 1.0) < 1e-10
        assert abs(res[4] - 2.0) < 1e-10
        assert abs(res[9] - 3.0) < 1e-10

    def test_batch_list(self):
        p1 = grid_packing(1)
        p4 = grid_packing(4)
        packings = [p1, p4]
        res = batch_container_side_lengths(packings)
        assert isinstance(res, list)
        assert len(res) == 2
        assert abs(res[0] - 1.0) < 1e-10
        assert abs(res[1] - 2.0) < 1e-10


class TestAuditSummary:
    """Tests for audit report formatting."""

    def test_audit_summary_valid(self):
        res = SubmissionAuditResult(
            valid=True,
            total_rows=500500,
            expected_rows=500500,
            unique_puzzles=1000,
            aggregate_score=22.2048027457,
            errors=[],
        )
        text = audit_summary(res)
        assert "PASS" in text
        assert "500,500" in text
        assert "22.2048027457" in text
        assert "Errors Found: `0`" in text

    def test_audit_summary_invalid(self):
        res = SubmissionAuditResult(
            valid=False,
            total_rows=100,
            expected_rows=500500,
            unique_puzzles=10,
            aggregate_score=float("inf"),
            errors=["Row count mismatch", "Missing puzzles"],
        )
        text = audit_summary(res)
        assert "FAIL" in text
        assert "Row count mismatch" in text
