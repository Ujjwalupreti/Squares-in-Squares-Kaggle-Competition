"""Configuration loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


# Default project root: two levels up from this file (src/squares_in_squares/)
_THIS_DIR = Path(__file__).resolve().parent
_DEFAULT_ROOT = _THIS_DIR.parent.parent


@dataclass
class Config:
    """Project-wide configuration."""

    # Puzzle range
    n_min: int = 1
    n_max: int = 1000

    # Optimization
    sa_initial_temp: float = 1.0
    sa_cooling_rate: float = 0.9999
    sa_min_temp: float = 1e-6
    sa_max_iterations: int = 100_000
    sa_time_limit_seconds: float = 60.0
    num_restarts: int = 3

    # Move parameters
    translate_step: float = 0.1
    rotate_step: float = 0.1
    move_decay: float = 0.999

    # Overlap penalty
    overlap_lambda: float = 1000.0

    # Validation
    sat_tolerance: float = 1e-9

    # Paths
    project_root: Path = field(default_factory=lambda: _DEFAULT_ROOT)
    artifacts_dir: Path = field(default=None)  # type: ignore[assignment]
    checkpoints_dir: Path = field(default=None)  # type: ignore[assignment]
    submissions_dir: Path = field(default=None)  # type: ignore[assignment]
    solutions_dir: Path = field(default=None)  # type: ignore[assignment]

    # Reproducibility
    random_seed: int = 42

    def __post_init__(self) -> None:
        if self.artifacts_dir is None:
            self.artifacts_dir = self.project_root / "artifacts"
        if self.checkpoints_dir is None:
            self.checkpoints_dir = self.project_root / "checkpoints"
        if self.submissions_dir is None:
            self.submissions_dir = self.project_root / "submissions"
        if self.solutions_dir is None:
            self.solutions_dir = self.project_root / "artifacts" / "solutions"
        self.validate()

    def validate(self) -> None:
        """Validate configuration values."""
        if not (1 <= self.n_min <= self.n_max <= 10000):
            raise ValueError(
                f"Invalid puzzle range: n_min={self.n_min}, n_max={self.n_max}"
            )
        if self.sa_initial_temp <= 0:
            raise ValueError(f"Initial temperature must be positive: {self.sa_initial_temp}")
        if not (0 < self.sa_cooling_rate < 1):
            raise ValueError(f"Cooling rate must be in (0,1): {self.sa_cooling_rate}")
        if self.sa_min_temp < 0:
            raise ValueError(f"Minimum temperature must be non-negative: {self.sa_min_temp}")
        if self.sa_max_iterations < 1:
            raise ValueError(f"Max iterations must be positive: {self.sa_max_iterations}")
        if self.sat_tolerance < 0:
            raise ValueError(f"SAT tolerance must be non-negative: {self.sat_tolerance}")
        if self.overlap_lambda < 0:
            raise ValueError(f"Overlap lambda must be non-negative: {self.overlap_lambda}")

    def ensure_dirs(self) -> None:
        """Create output directories if they don't exist."""
        for d in [self.artifacts_dir, self.checkpoints_dir,
                  self.submissions_dir, self.solutions_dir]:
            d.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        # Convert path strings to Path objects
        for key in ("project_root", "artifacts_dir", "checkpoints_dir",
                     "submissions_dir", "solutions_dir"):
            if key in data and isinstance(data[key], str):
                data[key] = Path(data[key])
        return cls(**data)

    @classmethod
    def default(cls) -> "Config":
        """Return a default configuration."""
        return cls()
