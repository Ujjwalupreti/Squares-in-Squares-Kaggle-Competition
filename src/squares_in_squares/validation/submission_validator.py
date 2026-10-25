"""Submission CSV structural and geometry validation.

Validates the complete submission CSV after generation and reload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .packing_validator import validate_packing_geometry, ValidationResult
from .score import puzzle_score


REQUIRED_COLUMNS = ["id", "n", "square_id", "x", "y", "angle"]
EXPECTED_TOTAL_ROWS = 500500  # sum(1..1000)


@dataclass
class SubmissionAuditResult:
    """Result of a complete submission audit."""
    valid: bool = False
    total_rows: int = 0
    expected_rows: int = EXPECTED_TOTAL_ROWS
    unique_puzzles: int = 0
    errors: list[str] = field(default_factory=list)
    puzzle_results: dict[int, ValidationResult] = field(default_factory=dict)
    aggregate_score: float = float('inf')


def audit_submission(
    csv_path: Path | str,
    n_min: int = 1,
    n_max: int = 1000,
    tolerance: float = 1e-9,
) -> SubmissionAuditResult:
    """Audit a submission CSV file.

    Checks:
    1. Column names and order.
    2. IDs are unique and sequential.
    3. Each puzzle has exactly n rows.
    4. Square IDs are complete (0..n-1).
    5. Total row count.
    6. All values are finite.
    7. Reconstructs and validates each packing geometry.
    8. Recomputes scores.

    Args:
        csv_path: path to the submission CSV.
        n_min: minimum puzzle size.
        n_max: maximum puzzle size.
        tolerance: SAT tolerance for geometry validation.

    Returns:
        SubmissionAuditResult with detailed error information.
    """
    result = SubmissionAuditResult()
    csv_path = Path(csv_path)

    # 1. Load CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        result.errors.append(f"Failed to read CSV: {e}")
        return result

    # 2. Check columns
    if list(df.columns) != REQUIRED_COLUMNS:
        result.errors.append(
            f"Column mismatch: expected {REQUIRED_COLUMNS}, got {list(df.columns)}"
        )
        return result

    result.total_rows = len(df)

    # 3. Check total row count
    expected = sum(range(n_min, n_max + 1))
    result.expected_rows = expected
    if result.total_rows != expected:
        result.errors.append(
            f"Row count mismatch: expected {expected}, got {result.total_rows}"
        )

    # 4. Check IDs are sequential
    expected_ids = list(range(result.total_rows))
    if list(df["id"]) != expected_ids:
        result.errors.append("IDs are not sequential starting from 0")

    # 5. Check finite values
    for col in ["x", "y", "angle"]:
        if not np.all(np.isfinite(df[col].values)):
            result.errors.append(f"Non-finite values found in column '{col}'")

    # 6. Per-puzzle validation
    scores = []
    puzzle_ns = sorted(df["n"].unique())
    result.unique_puzzles = len(puzzle_ns)

    for n in puzzle_ns:
        if n < n_min or n > n_max:
            result.errors.append(f"Unexpected puzzle size: n={n}")
            continue

        puzzle_df = df[df["n"] == n]

        # Check row count
        if len(puzzle_df) != n:
            result.errors.append(f"n={n}: expected {n} rows, got {len(puzzle_df)}")
            continue

        # Check square IDs
        square_ids = sorted(puzzle_df["square_id"].values)
        if square_ids != list(range(n)):
            result.errors.append(f"n={n}: square_ids not 0..{n-1}")
            continue

        # Reconstruct packing in square_id order
        puzzle_df_sorted = puzzle_df.sort_values("square_id")
        squares = puzzle_df_sorted[["x", "y", "angle"]].values.astype(np.float64)

        # Validate geometry
        vr = validate_packing_geometry(squares, n, tolerance=tolerance)
        result.puzzle_results[n] = vr

        if vr.valid:
            scores.append(vr.score)
        else:
            result.errors.append(f"n={n}: validation failed: {'; '.join(vr.errors)}")

    # Check all expected puzzles are present
    expected_ns = set(range(n_min, n_max + 1))
    missing = expected_ns - set(puzzle_ns)
    if missing:
        result.errors.append(f"Missing puzzles: {sorted(missing)[:10]}{'...' if len(missing) > 10 else ''}")

    # Compute aggregate score
    if scores:
        result.aggregate_score = sum(scores)

    result.valid = len(result.errors) == 0
    return result
