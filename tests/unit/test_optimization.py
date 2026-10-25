"""Unit tests for optimization algorithms and solvers."""

from __future__ import annotations

import numpy as np
import pytest

from squares_in_squares.optimization.annealing import simulated_annealing
from squares_in_squares.optimization.local_search import local_refinement
from squares_in_squares.optimization.restart import multi_start_optimize
from squares_in_squares.optimization.solver import solve_puzzle
from squares_in_squares.packing.grid import grid_packing
from squares_in_squares.validation.packing_validator import validate_packing_geometry
from squares_in_squares.config import Config


class TestOptimization:
    """Test suite for simulated annealing, local search, and solver orchestration."""

    def test_annealing_returns_valid_solution(self):
        initial = grid_packing(4)
        result = simulated_annealing(
            n=4,
            initial_squares=initial,
            max_iterations=100,
            time_limit=2.0,
            seed=42,
        )
        assert result.best_valid
        assert result.best_squares is not None
        assert result.best_squares.shape == (4, 3)
        assert result.best_L <= 2.0  # grid L is 2.0

        vr = validate_packing_geometry(result.best_squares, 4)
        assert vr.valid

    def test_local_refinement_maintains_validity(self):
        initial = grid_packing(4)
        refined, refined_L, iters = local_refinement(
            n=4,
            squares=initial,
            max_iterations=100,
            time_limit=2.0,
            seed=42,
        )
        assert refined.shape == (4, 3)
        assert refined_L <= 2.0
        vr = validate_packing_geometry(refined, 4)
        assert vr.valid

    def test_multi_start_returns_best_valid(self):
        result = multi_start_optimize(
            n=4,
            num_restarts=2,
            sa_kwargs=dict(max_iterations=100, time_limit=1.0),
            refine=True,
            refine_kwargs=dict(max_iterations=50, time_limit=0.5),
        )
        assert result.best_valid
        assert result.best_squares is not None
        assert result.best_L <= 2.0

    def test_solve_puzzle_baseline_only(self):
        res = solve_puzzle(4, use_optimization=False)
        assert res.valid
        assert res.strategy == "grid"
        assert res.container_length == pytest.approx(2.0)
        assert res.score == pytest.approx(0.0)

    def test_solve_puzzle_n1(self):
        res = solve_puzzle(1, use_optimization=True)
        assert res.valid
        assert res.container_length == pytest.approx(1.0)
        assert res.score == pytest.approx(0.0)
