"""Controlled benchmark experiments.

Runs standardized benchmarks with fixed puzzles, seeds, and budgets
to enable fair comparison of strategies.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..optimization.solver import solve_puzzle, SolverResult
from ..config import Config
from .metrics import MetricsLog, ExperimentRecord


@dataclass
class BenchmarkReport:
    """Summary of a benchmark run."""
    n_range: tuple[int, int]
    total_puzzles: int = 0
    valid_puzzles: int = 0
    baseline_aggregate: float = 0.0
    optimized_aggregate: float = 0.0
    improvement: float = 0.0
    total_runtime: float = 0.0
    results: list[SolverResult] | None = None


def run_benchmark(
    n_min: int = 1,
    n_max: int = 30,
    config: Config | None = None,
    use_optimization: bool = False,
    log_path: Path | None = None,
) -> BenchmarkReport:
    """Run a benchmark over a range of puzzle sizes.

    Args:
        n_min: smallest puzzle size.
        n_max: largest puzzle size.
        config: project configuration.
        use_optimization: whether to run optimization.
        log_path: path for experiment log.

    Returns:
        BenchmarkReport with aggregate results.
    """
    if config is None:
        config = Config.default()

    if log_path is None:
        log_path = config.artifacts_dir / "benchmark_log.jsonl"

    metrics = MetricsLog(log_path)
    report = BenchmarkReport(n_range=(n_min, n_max))
    results = []

    for n in range(n_min, n_max + 1):
        sr = solve_puzzle(n, config=config, use_optimization=use_optimization)
        results.append(sr)
        report.total_puzzles += 1

        if sr.valid:
            report.valid_puzzles += 1
            report.baseline_aggregate += sr.baseline_score
            if use_optimization:
                report.optimized_aggregate += sr.score
            else:
                report.optimized_aggregate += sr.score

        report.total_runtime += sr.runtime_seconds

        # Log the experiment
        metrics.record(ExperimentRecord(
            n=n,
            seed=sr.seed,
            strategy=sr.strategy,
            initial_L=sr.baseline_L,
            best_L=sr.container_length,
            score=sr.score,
            iterations=sr.iterations,
            runtime_seconds=sr.runtime_seconds,
            valid=sr.valid,
        ))

    report.improvement = report.baseline_aggregate - report.optimized_aggregate
    report.results = results
    return report
