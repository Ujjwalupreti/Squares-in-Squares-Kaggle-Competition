"""Resumable optimization checkpoints.

Checkpoints contain the full state needed to resume an interrupted
optimization run, including the random generator state.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np


CHECKPOINT_SCHEMA_VERSION = 1


@dataclass
class CheckpointData:
    """Serializable checkpoint state."""
    schema_version: int = CHECKPOINT_SCHEMA_VERSION
    n: int = 0
    seed: int = 42
    current_squares: list[list[float]] | None = None
    best_squares: list[list[float]] | None = None
    best_L: float = float('inf')
    best_score: float = float('inf')
    iteration: int = 0
    temperature: float = 1.0
    config_version: str = "1.0"
    created_at: str = ""
    rng_state: dict | None = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")


def save_checkpoint(
    path: Path,
    data: CheckpointData,
) -> None:
    """Save a checkpoint with atomic write.

    Args:
        path: checkpoint file path.
        data: checkpoint data to save.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")

    serializable = asdict(data)
    with open(tmp_path, "w") as f:
        json.dump(serializable, f, indent=2)
    tmp_path.replace(path)


def load_checkpoint(path: Path) -> CheckpointData | None:
    """Load a checkpoint, returning None if corrupted or incompatible.

    Args:
        path: checkpoint file path.

    Returns:
        CheckpointData or None.
    """
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if data.get("schema_version", 0) > CHECKPOINT_SCHEMA_VERSION:
            return None
        return CheckpointData(**{
            k: v for k, v in data.items()
            if k in CheckpointData.__dataclass_fields__
        })
    except (json.JSONDecodeError, TypeError, KeyError):
        return None
