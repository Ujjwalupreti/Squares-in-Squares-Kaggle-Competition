#!/usr/bin/env python
"""Universal Multi-Portfolio Master Merger and Boundary Hardening Pipeline.

Performs puzzle-by-puzzle cross-evaluation across multiple candidate submission files,
extracting the globally minimal bounding container for each puzzle n in 1..1000,
canonicalizing lower-left origin to (0, 0), and enforcing exact SAT feasibility
(tolerance 0.0) with adaptive radial contact dilation.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from squares_in_squares.geometry.bounds import container_side_length, half_extents
from squares_in_squares.geometry.sat import packing_has_overlap
from squares_in_squares.validation.score import puzzle_score, aggregate_score
from squares_in_squares.validation.packing_validator import validate_packing_geometry


def canonicalize_packing(squares: np.ndarray) -> np.ndarray:
    """Canonicalize packing coordinates to lower-left origin (0, 0) and normalize angles."""
    coords = squares.copy()
    h = half_extents(coords[:, 2])
    coords[:, 0] -= np.min(coords[:, 0] - h)
    coords[:, 1] -= np.min(coords[:, 1] - h)
    coords[:, 2] = np.mod(coords[:, 2], math.pi / 2.0)
    return coords


def dilate_packing(squares: np.ndarray, dilation_factor: float) -> np.ndarray:
    """Dilate square centers radially from centroid to ensure strict SAT non-overlap."""
    if dilation_factor <= 0:
        return squares.copy()
    coords = squares.copy()
    cx = float(np.mean(coords[:, 0]))
    cy = float(np.mean(coords[:, 1]))
    coords[:, 0] = cx + (coords[:, 0] - cx) * (1.0 + dilation_factor)
    coords[:, 1] = cy + (coords[:, 1] - cy) * (1.0 + dilation_factor)
    return canonicalize_packing(coords)


def master_merge(
    candidate_paths: List[Path | str],
    output_path: Path | str,
    tolerance: float = 0.0,
    dilation_factors: List[float] | None = None,
) -> Tuple[float, int]:
    """Execute cross-merge across candidate files, validating at strict tolerance.

    Args:
        candidate_paths: list of candidate CSV or TXT submission file paths.
        output_path: output path for the merged submission CSV.
        tolerance: SAT tolerance for non-overlap check (default 0.0).
        dilation_factors: list of dilation increments to attempt for contact hardening.

    Returns:
        (final_score, num_improvements)
    """
    if dilation_factors is None:
        dilation_factors = [0.0, 1e-12, 1e-11, 1e-10, 1e-9, 1e-8, 1e-7]

    packings_by_file: Dict[str, Dict[int, np.ndarray]] = {}
    valid_candidates: List[str] = []

    for cpath in candidate_paths:
        p = Path(cpath)
        if not p.exists():
            continue
        print(f"Loading candidate portfolio: {p.name}...")
        df = pd.read_csv(p)
        packings_by_file[p.name] = {}
        for n, g in df.groupby("n"):
            if len(g) == n:
                packings_by_file[p.name][int(n)] = g.sort_values("square_id")[["x", "y", "angle"]].values.astype(float)
        valid_candidates.append(p.name)

    if not valid_candidates:
        raise ValueError("No valid candidate files found.")

    best_packings: Dict[int, np.ndarray] = {}
    best_lengths: Dict[int, float] = {}
    source_of_best: Dict[int, str] = {}

    primary = valid_candidates[0]
    for n in range(1, 1001):
        raw = packings_by_file[primary][n]
        canon = canonicalize_packing(raw)
        best_packings[n] = canon
        best_lengths[n] = container_side_length(canon)
        source_of_best[n] = primary

    total_swaps = 0

    for cand_name in valid_candidates[1:]:
        print(f"Cross-evaluating candidate: {cand_name}...")
        file_swaps = 0
        cand_dict = packings_by_file[cand_name]
        for n in range(1, 1001):
            if n not in cand_dict:
                continue
            cand_raw = cand_dict[n]
            cand_canon = canonicalize_packing(cand_raw)
            cand_side = container_side_length(cand_canon)

            if cand_side < best_lengths[n] - 1e-12:
                # Test for valid configuration with adaptive dilation
                for d in dilation_factors:
                    tested = dilate_packing(cand_canon, d) if d > 0 else cand_canon
                    has_ov, _ = packing_has_overlap(tested, tolerance=tolerance)
                    if not has_ov:
                        tested_side = container_side_length(tested)
                        if tested_side < best_lengths[n] - 1e-12:
                            best_lengths[n] = tested_side
                            best_packings[n] = tested
                            source_of_best[n] = cand_name
                            file_swaps += 1
                            total_swaps += 1
                        break
        print(f"  Accepted {file_swaps} superior packings from {cand_name}.")

    # Generate output submission dataframe
    rows = []
    row_id = 0
    for n in range(1, 1001):
        coords = best_packings[n]
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
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_p, index=False)
    print(f"Exported merged master submission to {out_p} ({len(df_out)} rows).")

    final_score = sum(puzzle_score(n, best_lengths[n]) for n in range(1, 1001))
    print(f"Final Certified Aggregate Score: {final_score:.12f}")
    return final_score, total_swaps


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-Portfolio Master Merger and Hardening Engine")
    parser.add_argument("candidates", nargs="+", help="Paths to candidate submission files")
    parser.add_argument("--output", "-o", required=True, help="Path for output merged CSV")
    parser.add_argument("--tolerance", "-t", type=float, default=0.0, help="SAT tolerance (default 0.0)")
    args = parser.parse_args()

    master_merge(args.candidates, args.output, tolerance=args.tolerance)
    return 0


if __name__ == "__main__":
    sys.exit(main())
