#!/usr/bin/env python
"""Automated greedy packing merger and safe contact dilation optimizer.

Performs puzzle-by-puzzle evaluation and merges tighter valid packings
into the submission file, applying boundary dilation to guarantee zero-overlap.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure src is in sys.path
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from squares_in_squares.geometry.bounds import container_side_length
from squares_in_squares.validation.packing_validator import validate_packing_geometry


def compute_side(squares: np.ndarray) -> float:
    """Compute bounding container side length for square packing."""
    c = np.cos(squares[:, 2])
    s = np.sin(squares[:, 2])
    h = 0.5 * (np.abs(c) + np.abs(s))
    min_x = np.min(squares[:, 0] - h)
    max_x = np.max(squares[:, 0] + h)
    min_y = np.min(squares[:, 1] - h)
    max_y = np.max(squares[:, 1] + h)
    return float(max(max_x - min_x, max_y - min_y))


def merge_packings(
    base_csv: Path | str,
    candidate_file: Path | str,
    output_csv: Path | str | None = None,
    dilation_factor: float = 1e-10,
    tolerance: float = 0.0,
    report_path: Path | str | None = None,
    dry_run: bool = False,
) -> tuple[float, float, int]:
    """Merge candidate packings into base submission if strictly superior and collision-free."""
    base_csv = Path(base_csv)
    candidate_file = Path(candidate_file)
    if output_csv is not None:
        output_csv = Path(output_csv)

    print(f"Loading base submission: {base_csv}...")
    df_base = pd.read_csv(base_csv)
    base_packings = {}
    for n, g in df_base.groupby("n"):
        base_packings[int(n)] = g.sort_values("square_id")[["x", "y", "angle"]].values.astype(float)

    print(f"Loading candidate packings: {candidate_file}...")
    df_cand = pd.read_csv(candidate_file)
    cand_packings = {}
    for n, g in df_cand.groupby("n"):
        if len(g) == n:
            cand_packings[int(n)] = g.sort_values("square_id")[["x", "y", "angle"]].values.astype(float)

    init_score = sum(compute_side(base_packings[n]) / math.sqrt(n) - 1.0 for n in range(1, 1001))
    print(f"Initial aggregate score: {init_score:.8f}")

    improvements = []
    rejected_overlaps = []
    for n in range(1, 1001):
        curr_side = compute_side(base_packings[n])
        if n in cand_packings:
            cand_side = compute_side(cand_packings[n])
            if cand_side < curr_side - 1e-6:
                # Rigorous SAT feasibility check before accepting
                vr = validate_packing_geometry(cand_packings[n], n, tolerance=tolerance)
                if vr.valid:
                    gain = (curr_side - cand_side) / math.sqrt(n)
                    improvements.append((n, curr_side, cand_side, gain))
                    base_packings[n] = cand_packings[n]
                else:
                    rejected_overlaps.append((n, curr_side, cand_side, vr.errors))

    print(f"Accepted {len(improvements)} strictly superior collision-free configurations.")
    if rejected_overlaps:
        print(f"Rejected {len(rejected_overlaps)} candidate configurations due to SAT collision/overlap.")
        for n, old_l, cand_l, errs in rejected_overlaps[:5]:
            print(f"  [REJECTED] n={n:3d}: proposed L {cand_l:.5f} < {old_l:.5f} but failed: {errs}")

    for n, old_l, new_l, g in improvements[:15]:
        print(f"  n={n:3d}: L {old_l:.5f} -> {new_l:.5f} (gain: {g:.6f})")
    if len(improvements) > 15:
        print(f"  ... and {len(improvements) - 15} more improvements.")

    new_score = sum(compute_side(base_packings[n]) / math.sqrt(n) - 1.0 for n in range(1, 1001))
    print(f"\nNet improvement: -{init_score - new_score:.8f}")
    print(f"New aggregate score: {new_score:.8f}")

    if report_path is not None:
        report_p = Path(report_path)
        report_p.parent.mkdir(parents=True, exist_ok=True)
        with open(report_p, "w", encoding="utf-8") as f:
            f.write("# Merge & Optimization Audit Report\n\n")
            f.write(f"- Base submission: `{base_csv.name}`\n")
            f.write(f"- Candidate file: `{candidate_file.name}`\n")
            f.write(f"- Initial score: `{init_score:.8f}`\n")
            f.write(f"- New score: `{new_score:.8f}`\n")
            f.write(f"- Net score reduction: `-{init_score - new_score:.8f}`\n")
            f.write(f"- Accepted upgrades: `{len(improvements)}`\n")
            f.write(f"- Rejected overlaps: `{len(rejected_overlaps)}`\n\n")
            f.write("## Top Accepted Improvements\n\n")
            f.write("| Puzzle $n$ | Previous $L$ | New $L$ | Score Gain |\n| :---: | :---: | :---: | :---: |\n")
            for n, old_l, new_l, g in sorted(improvements, key=lambda x: x[3], reverse=True)[:25]:
                f.write(f"| {n} | {old_l:.6f} | {new_l:.6f} | {g:.8f} |\n")
        print(f"Wrote audit report to {report_p}.")

    if dry_run or output_csv is None:
        print("Dry run requested; no submission file written.")
        return init_score, new_score, len(improvements)

    # Build submission with center dilation for exact contact safety
    print(f"Writing output to {output_csv} (dilation={dilation_factor})...")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    row_id = 0
    for n in range(1, 1001):
        coords = base_packings[n].copy()
        is_grid = np.all(np.abs(coords[:, 2]) < 1e-4) and abs(compute_side(coords) - round(compute_side(coords))) < 1e-4
        if not is_grid and dilation_factor > 0:
            center = coords[:, :2].mean(axis=0)
            coords[:, :2] = center + (coords[:, :2] - center) * (1.0 + dilation_factor)

        # Analytical N=5 safeguard for strict mpmath interval arithmetic
        if n == 5:
            L5 = 2.0 + 1.0 / math.sqrt(2.0) + 1e-7
            coords = np.array([
                [0.5, 0.5, 0.0],
                [L5 - 0.5, 0.5, 0.0],
                [0.5, L5 - 0.5, 0.0],
                [L5 - 0.5, L5 - 0.5, 0.0],
                [L5 / 2.0, L5 / 2.0, math.pi / 4.0],
            ], dtype=float)

        # Canonicalize to lower-left origin
        c = np.abs(np.cos(coords[:, 2]))
        s = np.abs(np.sin(coords[:, 2]))
        h = 0.5 * (c + s)
        min_x = np.min(coords[:, 0] - h)
        min_y = np.min(coords[:, 1] - h)
        coords[:, 0] -= min_x
        coords[:, 1] -= min_y
        coords[:, 2] = np.mod(coords[:, 2], math.pi / 2.0)

        for sid in range(n):
            rows.append({
                "id": row_id,
                "n": n,
                "square_id": sid,
                "x": float(coords[sid, 0]),
                "y": float(coords[sid, 1]),
                "angle": float(coords[sid, 2]),
            })
            row_id += 1

    df_out = pd.DataFrame(rows)
    df_out.to_csv(output_csv, index=False)
    print(f"Successfully generated {output_csv.name} ({len(df_out)} rows).")

    return init_score, new_score, len(improvements)


def main() -> int:
    parser = argparse.ArgumentParser(description="Greedy packing merger and dilation optimizer")
    parser.add_argument("--base", type=str, default="submissions/submission_improved.csv",
                        help="Path to base submission CSV")
    parser.add_argument("--candidate", type=str, default="../top_score_file.txt",
                        help="Path to candidate packings CSV/TXT")
    parser.add_argument("--output", type=str, default="submissions/submission_improved.csv",
                        help="Path to output submission CSV")
    parser.add_argument("--dilation", type=float, default=1e-10,
                        help="Contact dilation factor for float64 safety")
    parser.add_argument("--tolerance", type=float, default=0.0,
                        help="Collision tolerance for SAT checks (default 0.0)")
    parser.add_argument("--report", type=str, default=None,
                        help="Optional path to output markdown audit report")
    parser.add_argument("--dry-run", action="store_true",
                        help="Evaluate merge without writing output file")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    base_p = (repo_root / args.base).resolve()
    cand_p = (repo_root / args.candidate).resolve()
    out_p = (repo_root / args.output).resolve() if args.output else None
    rep_p = (repo_root / args.report).resolve() if args.report else None

    merge_packings(
        base_p,
        cand_p,
        out_p,
        dilation_factor=args.dilation,
        tolerance=args.tolerance,
        report_path=rep_p,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
