"""Final submission audit.

Reloads a generated CSV and performs a complete structural and
geometric audit, independent of the generation process.
"""

from __future__ import annotations

from pathlib import Path

from ..validation.submission_validator import audit_submission, SubmissionAuditResult


def audit_submission_file(
    csv_path: Path | str,
    n_min: int = 1,
    n_max: int = 1000,
    tolerance: float = 1e-9,
) -> SubmissionAuditResult:
    """Run a full audit on a submission CSV file.

    This is the final gate before considering a submission ready.

    Args:
        csv_path: path to the submission CSV.
        n_min: minimum puzzle size.
        n_max: maximum puzzle size.
        tolerance: SAT tolerance.

    Returns:
        SubmissionAuditResult with full details.
    """
    return audit_submission(csv_path, n_min=n_min, n_max=n_max, tolerance=tolerance)
