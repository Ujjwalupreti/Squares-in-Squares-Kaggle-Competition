"""Score and runtime metrics tracking."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ExperimentRecord:
    """One experiment result per puzzle and run."""
    n: int
    seed: int
    strategy: str
    initial_L: float
    best_L: float
    score: float
    iterations: int
    runtime_seconds: float
    valid: bool
    config_version: str = "1.0"
    code_revision: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")


class MetricsLog:
    """Append-only experiment metrics log."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, experiment: ExperimentRecord) -> None:
        """Append an experiment record to the log."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(asdict(experiment)) + "\n")

    def load_all(self) -> list[ExperimentRecord]:
        """Load all experiment records from the log."""
        if not self.log_path.exists():
            return []
        records = []
        with open(self.log_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        records.append(ExperimentRecord(**{
                            k: v for k, v in data.items()
                            if k in ExperimentRecord.__dataclass_fields__
                        }))
                    except (json.JSONDecodeError, TypeError):
                        continue
        return records
