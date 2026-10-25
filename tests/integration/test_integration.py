"""Integration tests for baseline, optimization, checkpoint, and submission."""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

import numpy as np
import pytest

from squares_in_squares.packing.grid import grid_packing
from squares_in_squares.validation.packing_validator import validate_packing_geometry
from squares_in_squares.validation.score import puzzle_score
from squares_in_squares.geometry.bounds import container_side_length
from squares_in_squares.geometry.sat import packing_has_overlap
from squares_in_squares.storage.solution_store import SolutionStore, SolutionRecord
from squares_in_squares.storage.checkpoint import (
    save_checkpoint, load_checkpoint, CheckpointData,
)
from squares_in_squares.submission.build_submission import build_submission
from squares_in_squares.validation.submission_validator import audit_submission
from squares_in_squares.config import Config


# ==================== Baseline Tests ====================

class TestBaseline:
    """Tests for grid baseline generation."""

    def test_n1(self):
        s = grid_packing(1)
        assert s.shape == (1, 3)
        vr = validate_packing_geometry(s, 1)
        assert vr.valid

    def test_n4(self):
        """4 squares in a 2x2 grid."""
        s = grid_packing(4)
        assert s.shape == (4, 3)
        vr = validate_packing_geometry(s, 4)
        assert vr.valid
        assert abs(vr.container_length - 2.0) < 1e-10

    def test_n9(self):
        """9 squares in a 3x3 grid."""
        s = grid_packing(9)
        vr = validate_packing_geometry(s, 9)
        assert vr.valid
        assert abs(vr.container_length - 3.0) < 1e-10

    @pytest.mark.parametrize("n", [1, 2, 3, 5, 10, 25, 50, 100])
    def test_baseline_valid(self, n):
        """Baseline is valid for various n."""
        s = grid_packing(n)
        vr = validate_packing_geometry(s, n)
        assert vr.valid, f"n={n}: {vr.errors}"

    def test_baseline_all_small(self):
        """Baseline valid for n=1..50."""
        for n in range(1, 51):
            s = grid_packing(n)
            vr = validate_packing_geometry(s, n)
            assert vr.valid, f"n={n}: {vr.errors}"

    def test_baseline_scores_finite(self):
        """All baseline scores must be finite."""
        for n in range(1, 51):
            s = grid_packing(n)
            L = container_side_length(s)
            score = puzzle_score(n, L)
            assert math.isfinite(score), f"n={n}: score={score}"


# ==================== Solution Store Tests ====================

class TestSolutionStore:
    """Tests for solution persistence."""

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SolutionStore(Path(tmpdir))
            record = SolutionRecord(
                n=4,
                squares=[[0.5, 0.5, 0.0], [1.5, 0.5, 0.0],
                         [0.5, 1.5, 0.0], [1.5, 1.5, 0.0]],
                container_length=2.0,
                score=0.0,
                seed=42,
                strategy="grid",
                runtime_seconds=0.1,
            )
            store.save(record)
            loaded = store.load(4)
            assert loaded is not None
            assert loaded.n == 4
            assert loaded.score == 0.0

    def test_never_overwrites_better(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SolutionStore(Path(tmpdir))
            good = SolutionRecord(
                n=4, squares=[[0.5, 0.5, 0.0]] * 4,
                container_length=2.0, score=0.0,
                seed=42, strategy="grid", runtime_seconds=0.1,
            )
            worse = SolutionRecord(
                n=4, squares=[[0.5, 0.5, 0.0]] * 4,
                container_length=3.0, score=0.5,
                seed=42, strategy="grid", runtime_seconds=0.1,
            )
            store.save(good)
            store.save(worse)  # Should not overwrite
            loaded = store.load(4)
            assert loaded.score == 0.0

    def test_load_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SolutionStore(Path(tmpdir))
            assert store.load(999) is None

    def test_load_squares(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SolutionStore(Path(tmpdir))
            record = SolutionRecord(
                n=2,
                squares=[[0.5, 0.5, 0.0], [1.5, 0.5, 0.0]],
                container_length=2.0,
                score=puzzle_score(2, 2.0),
                seed=42, strategy="grid", runtime_seconds=0.01,
            )
            store.save(record)
            squares = store.load_squares(2)
            assert squares is not None
            assert squares.shape == (2, 3)

    def test_list_solutions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SolutionStore(Path(tmpdir))
            for n in [1, 5, 10]:
                record = SolutionRecord(
                    n=n, squares=[[0.5, 0.5, 0.0]] * n,
                    container_length=float(n), score=0.1,
                    seed=42, strategy="grid", runtime_seconds=0.01,
                )
                store.save(record)
            assert store.list_solutions() == [1, 5, 10]


# ==================== Checkpoint Tests ====================

class TestCheckpoint:
    """Tests for checkpoint persistence."""

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "checkpoint.json"
            data = CheckpointData(
                n=10,
                seed=42,
                current_squares=[[0.5, 0.5, 0.0]] * 10,
                best_squares=[[0.5, 0.5, 0.0]] * 10,
                best_L=5.0,
                iteration=1000,
                temperature=0.1,
            )
            save_checkpoint(path, data)
            loaded = load_checkpoint(path)
            assert loaded is not None
            assert loaded.n == 10
            assert loaded.iteration == 1000

    def test_load_nonexistent(self):
        path = Path("/nonexistent/checkpoint.json")
        assert load_checkpoint(path) is None

    def test_corrupted_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "checkpoint.json"
            with open(path, "w") as f:
                f.write("not json")
            assert load_checkpoint(path) is None


# ==================== Submission Tests ====================

class TestSubmission:
    """Tests for CSV generation and audit."""

    def test_small_submission(self):
        """Build and audit a submission for n=1..5."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            store = SolutionStore(tmpdir / "solutions")

            for n in range(1, 6):
                s = grid_packing(n)
                L = container_side_length(s)
                record = SolutionRecord(
                    n=n,
                    squares=s.tolist(),
                    container_length=L,
                    score=puzzle_score(n, L),
                    seed=42,
                    strategy="grid",
                    runtime_seconds=0.01,
                )
                store.save(record)

            csv_path = tmpdir / "submission.csv"
            success, total_rows, missing = build_submission(
                store, csv_path, n_min=1, n_max=5,
            )
            assert success
            assert total_rows == 15  # 1+2+3+4+5
            assert missing == []

            # Audit
            result = audit_submission(csv_path, n_min=1, n_max=5)
            assert result.valid, f"Audit errors: {result.errors}"
            assert result.total_rows == 15
            assert result.unique_puzzles == 5

    def test_missing_puzzles(self):
        """Submission with missing puzzles reports them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            store = SolutionStore(tmpdir / "solutions")

            # Only save n=1,3
            for n in [1, 3]:
                s = grid_packing(n)
                L = container_side_length(s)
                record = SolutionRecord(
                    n=n, squares=s.tolist(),
                    container_length=L, score=puzzle_score(n, L),
                    seed=42, strategy="grid", runtime_seconds=0.01,
                )
                store.save(record)

            csv_path = tmpdir / "submission.csv"
            success, total_rows, missing = build_submission(
                store, csv_path, n_min=1, n_max=5,
            )
            assert not success
            assert 2 in missing
            assert 4 in missing
            assert 5 in missing
