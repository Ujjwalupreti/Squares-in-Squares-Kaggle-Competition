"""Unit tests for benchmark and metrics logging."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from squares_in_squares.experiments.metrics import ExperimentRecord, MetricsLog
from squares_in_squares.experiments.benchmark import run_benchmark, BenchmarkReport
from squares_in_squares.config import Config


class TestMetricsAndBenchmark:
    """Test suite for metrics recording and controlled benchmarks."""

    def test_metrics_log_record_and_load(self, tmp_path: Path):
        log_file = tmp_path / "test_log.jsonl"
        log = MetricsLog(log_file)

        assert log.load_all() == []

        rec1 = ExperimentRecord(
            n=2,
            seed=42,
            strategy="grid",
            initial_L=2.0,
            best_L=2.0,
            score=0.4142,
            iterations=0,
            runtime_seconds=0.01,
            valid=True,
        )
        rec2 = ExperimentRecord(
            n=3,
            seed=42,
            strategy="sa",
            initial_L=2.0,
            best_L=1.95,
            score=0.125,
            iterations=100,
            runtime_seconds=0.05,
            valid=True,
        )
        log.record(rec1)
        log.record(rec2)

        loaded = log.load_all()
        assert len(loaded) == 2
        assert loaded[0].n == 2
        assert loaded[0].strategy == "grid"
        assert loaded[1].n == 3
        assert loaded[1].best_L == pytest.approx(1.95)

    def test_run_benchmark_small(self, tmp_path: Path):
        cfg = Config(
            n_min=2,
            n_max=3,
            sa_max_iterations=50,
            sa_time_limit_seconds=1.0,
            artifacts_dir=tmp_path / "artifacts",
            solutions_dir=tmp_path / "solutions",
        )
        report = run_benchmark(
            n_min=2,
            n_max=3,
            config=cfg,
            use_optimization=False,
            log_path=tmp_path / "bench.jsonl",
        )

        assert report.total_puzzles == 2
        assert report.valid_puzzles == 2
        assert report.baseline_aggregate > 0
        assert (tmp_path / "bench.jsonl").exists()
