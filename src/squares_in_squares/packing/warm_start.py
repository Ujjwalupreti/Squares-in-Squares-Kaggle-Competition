"""Warm-start from previously saved feasible solutions."""

from __future__ import annotations

from pathlib import Path

import json
import numpy as np


def load_solution(path: Path) -> np.ndarray | None:
    """Load a saved solution from a JSON file.

    Args:
        path: path to the solution JSON file.

    Returns:
        Array of shape (n, 3) or None if file doesn't exist.
    """
    if not path.exists():
        return None
    with open(path, "r") as f:
        data = json.load(f)
    squares_data = data.get("squares")
    if squares_data is None:
        return None
    return np.array(squares_data, dtype=np.float64)


def warm_start_packing(n: int, solutions_dir: Path) -> np.ndarray | None:
    """Load a previously saved solution as a warm start.

    Args:
        n: puzzle size.
        solutions_dir: directory containing solution JSON files.

    Returns:
        Array of shape (n, 3) or None if no saved solution.
    """
    path = solutions_dir / f"solution_n{n:04d}.json"
    solution = load_solution(path)
    if solution is not None and solution.shape == (n, 3):
        return solution
    return None
