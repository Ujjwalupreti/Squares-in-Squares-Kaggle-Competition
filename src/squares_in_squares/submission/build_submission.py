"""CSV submission builder.

Generates a CSV with exactly the required columns:
    id,n,square_id,x,y,angle

For each puzzle n, includes n rows with square_ids 0..n-1.
IDs are unique sequential integers starting from 0.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..storage.solution_store import SolutionStore


def build_submission(
    store: SolutionStore,
    output_path: Path,
    n_min: int = 1,
    n_max: int = 1000,
) -> tuple[bool, int, list[int]]:
    """Build a submission CSV from the solution store.

    Args:
        store: solution store containing validated solutions.
        output_path: path for the output CSV.
        n_min: minimum puzzle size.
        n_max: maximum puzzle size.

    Returns:
        (success, total_rows, missing_puzzles)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    row_id = 0
    missing = []

    for n in range(n_min, n_max + 1):
        squares = store.load_squares(n)
        if squares is None:
            missing.append(n)
            continue

        for square_id in range(n):
            rows.append({
                "id": row_id,
                "n": n,
                "square_id": square_id,
                "x": float(squares[square_id, 0]),
                "y": float(squares[square_id, 1]),
                "angle": float(squares[square_id, 2]),
            })
            row_id += 1

    if not rows:
        return False, 0, missing

    df = pd.DataFrame(rows, columns=["id", "n", "square_id", "x", "y", "angle"])
    df.to_csv(output_path, index=False)

    # Compute overall score for convenience
    total_score = 0.0
    for n in range(n_min, n_max + 1):
        rec = store.load(n)
        if rec is not None:
            total_score += rec.score

    if len(missing) == 0:
        print(f"Successfully generated {output_path} ({len(rows):,} rows, 1,000 puzzles, total score: {total_score:.10f})")

    return len(missing) == 0, len(rows), missing
