#!/usr/bin/env python
"""Ingest solutions from an external submission file into the SolutionStore.

Only replaces an incumbent if the incoming solution is independently
validated and strictly improves upon the current best score.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure src is in sys.path
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from squares_in_squares.config import Config
from squares_in_squares.storage.solution_store import SolutionStore, SolutionRecord
from squares_in_squares.validation.packing_validator import validate_packing_geometry


def ingest_file(
    file_path: Path | str,
    config: Config | None = None,
    tolerance: float = 1e-9,
) -> tuple[int, int, float, float]:
    """Ingest solutions from a CSV or text submission file.

    Args:
        file_path: Path to the submission file.
        config: Project configuration.
        tolerance: SAT tolerance for validation.

    Returns:
        (total_puzzles, improved_count, old_total_score, new_total_score)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if config is None:
        config = Config.default()
    config.ensure_dirs()
    store = SolutionStore(config.solutions_dir)

    print(f"Loading submission file: {file_path}...")
    df = pd.read_csv(file_path)

    # Invariants check
    req_cols = ["id", "n", "square_id", "x", "y", "angle"]
    if list(df.columns) != req_cols:
        raise ValueError(f"Columns mismatch: expected {req_cols}, got {list(df.columns)}")

    puzzle_ns = sorted(df["n"].unique())
    print(f"Found {len(puzzle_ns)} unique puzzles. Ingesting improvements...")

    improved_count = 0
    total_saved = 0
    old_total_score = 0.0
    new_total_score = 0.0

    start_time = time.time()

    for n_val in puzzle_ns:
        n = int(n_val)
        existing = store.load(n)
        current_score = existing.score if existing else float("inf")
        old_total_score += current_score if current_score != float("inf") else 0.0

        puzzle_df = df[df["n"] == n].sort_values("square_id")
        if len(puzzle_df) != n:
            print(f"Warning: n={n} has {len(puzzle_df)} rows, expected {n}. Skipping.")
            new_total_score += current_score
            continue

        squares = puzzle_df[["x", "y", "angle"]].values.astype(np.float64)

        # Fast preliminary bounds check
        h = (np.abs(np.cos(squares[:, 2])) + np.abs(np.sin(squares[:, 2]))) / 2.0
        width = np.max(squares[:, 0] + h) - np.min(squares[:, 0] - h)
        height = np.max(squares[:, 1] + h) - np.min(squares[:, 1] - h)
        cand_L = float(max(width, height))
        cand_score = float(cand_L / np.sqrt(n) - 1.0)

        if cand_score < current_score - 1e-12:
            # Strictly better score, validate geometry
            vr = validate_packing_geometry(squares, n, tolerance=tolerance)
            if vr.valid:
                record = SolutionRecord(
                    n=n,
                    squares=[[float(c) for c in row] for row in squares],
                    container_length=float(vr.container_length),
                    score=float(vr.score),
                    seed=0,
                    strategy="ingested_top_score",
                    runtime_seconds=0.0,
                )
                store.save(record)
                improved_count += 1
                new_total_score += vr.score
                if improved_count <= 20 or improved_count % 50 == 0:
                    diff = current_score - vr.score
                    print(
                        f"  [Improved] n={n:4d}: score {current_score:.4f} -> {vr.score:.4f} "
                        f"(diff: -{diff:.6f}, L={vr.container_length:.4f})"
                    )
            else:
                print(f"  [Invalid] n={n}: candidate improved score but failed geometry: {vr.errors}")
                new_total_score += current_score
        else:
            new_total_score += current_score

    elapsed = time.time() - start_time
    print(f"\nIngestion complete in {elapsed:.2f}s:")
    print(f"  Puzzles processed: {len(puzzle_ns)}")
    print(f"  Puzzles improved:  {improved_count}")
    print(f"  Old total score:   {old_total_score:.6f}")
    print(f"  New total score:   {new_total_score:.6f}")
    print(f"  Net improvement:   {old_total_score - new_total_score:.6f}")

    return len(puzzle_ns), improved_count, old_total_score, new_total_score


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest solutions into SolutionStore")
    parser.add_argument("file", type=str, help="Path to submission CSV or TXT file")
    parser.add_argument("--config", "-c", type=str, help="Path to config YAML")
    args = parser.parse_args()

    cfg = Config.from_yaml(args.config) if args.config else Config.default()
    ingest_file(args.file, config=cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
