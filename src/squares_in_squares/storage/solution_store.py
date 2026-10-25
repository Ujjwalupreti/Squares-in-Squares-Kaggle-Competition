"""Best-valid-solution store.

Stores the best validated solution for each puzzle size n.
Solutions are saved as JSON files with metadata.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np


SCHEMA_VERSION = 1


@dataclass
class SolutionRecord:
    """A validated solution record."""
    n: int
    squares: list[list[float]]  # [[x, y, angle], ...]
    container_length: float
    score: float
    seed: int
    strategy: str
    runtime_seconds: float
    validator_version: str = "1.0"
    schema_version: int = SCHEMA_VERSION
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")


class SolutionStore:
    """Persistent store for the best validated solution per puzzle."""

    def __init__(self, solutions_dir: Path):
        self.solutions_dir = solutions_dir
        self.solutions_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, n: int) -> Path:
        return self.solutions_dir / f"solution_n{n:04d}.json"

    def save(self, record: SolutionRecord) -> None:
        """Save a solution record, overwriting only if it's better.

        Never overwrites a valid incumbent with a worse solution.

        Args:
            record: the solution to save.
        """
        path = self._path(record.n)

        # Check existing
        existing = self.load(record.n)
        if existing is not None:
            if existing.score <= record.score:
                return  # Existing solution is as good or better

        # Atomic-ish write: write to temp then rename
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(asdict(record), f, indent=2)
        tmp_path.replace(path)

    def load(self, n: int) -> SolutionRecord | None:
        """Load a saved solution for puzzle size n.

        Args:
            n: puzzle size.

        Returns:
            SolutionRecord or None if not found or corrupted.
        """
        path = self._path(n)
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                data = json.load(f)
            # Validate schema
            if data.get("schema_version", 0) > SCHEMA_VERSION:
                return None  # Incompatible future version
            return SolutionRecord(**{
                k: v for k, v in data.items()
                if k in SolutionRecord.__dataclass_fields__
            })
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def load_squares(self, n: int) -> np.ndarray | None:
        """Load just the squares array for puzzle size n.

        Returns:
            Array of shape (n, 3) or None.
        """
        record = self.load(n)
        if record is None:
            return None
        squares = np.array(record.squares, dtype=np.float64)
        if squares.shape != (n, 3):
            return None
        return squares

    def has_solution(self, n: int) -> bool:
        """Check if a solution exists for puzzle size n."""
        return self._path(n).exists()

    def get_score(self, n: int) -> float:
        """Get the stored score for puzzle size n."""
        record = self.load(n)
        if record is None:
            return float('inf')
        return record.score

    def list_solutions(self) -> list[int]:
        """List all puzzle sizes with saved solutions."""
        solutions = []
        for path in self.solutions_dir.glob("solution_n*.json"):
            try:
                # Filename is solution_n0001.json => extract "0001"
                stem = path.stem  # e.g., "solution_n0001"
                num_str = stem.replace("solution_n", "", 1)
                n = int(num_str)
                solutions.append(n)
            except (ValueError, IndexError):
                continue
        return sorted(solutions)
