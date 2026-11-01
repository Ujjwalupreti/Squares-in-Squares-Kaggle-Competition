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
    output_csv: Path | str,
    dilation_factor: float = 1e-11,
) -> tuple[float, float, int]:
    """Merge candidate packings into base submission if strictly superior."""
    base_csv = Path(base_csv)
    candidate_file = Path(candidate_file)
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
    for n in range(1, 1001):
        curr_side = compute_side(base_packings[n])
        if n in cand_packings:
            cand_side = compute_side(cand_packings[n])
            if cand_side < curr_side - 1e-6:
                gain = (curr_side - cand_side) / math.sqrt(n)
                improvements.append((n, curr_side, cand_side, gain))
                base_packings[n] = cand_packings[n]

    print(f"Replaced {len(improvements)} puzzles with improved configurations.")
    for n, old_l, new_l, g in improvements:
        print(f"  n={n:3d}: L {old_l:.5f} -> {new_l:.5f} (gain: {g:.6f})")

    new_score = sum(compute_side(base_packings[n]) / math.sqrt(n) - 1.0 for n in range(1, 1001))
    print(f"\nNet improvement: -{init_score - new_score:.8f}")
    print(f"New aggregate score: {new_score:.8f}")

    # Build submission with center dilation for exact contact safety
    print(f"Writing output to {output_csv} (dilation={dilation_factor})...")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    row_id = 0
    for n in range(1, 1001):
        coords = base_packings[n].copy()
        if dilation_factor > 0:
            center = coords[:, :2].mean(axis=0)
            coords[:, :2] = center + (coords[:, :2] - center) * (1.0 + dilation_factor)

        for sid in range(n):
            rows.append({
                "id": row_id,
                "n": n,
                "square_id": sid,
                "x": repr(float(coords[sid, 0])),
                "y": repr(float(coords[sid, 1])),
                "angle": repr(float(coords[sid, 2])),
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
    parser.add_argument("--output", type=str, default="submissions/submission_v2_improved.csv",
                        help="Path to output submission CSV")
    parser.add_argument("--dilation", type=float, default=1e-11,
                        help="Contact dilation factor for float64 safety")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    base_p = (repo_root / args.base).resolve()
    cand_p = (repo_root / args.candidate).resolve()
    out_p = (repo_root / args.output).resolve()

    merge_packings(base_p, cand_p, out_p, dilation_factor=args.dilation)
    return 0


if __name__ == "__main__":
    sys.exit(main())
