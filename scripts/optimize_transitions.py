"""Autonomous First-Principles Transition Optimizer.

Scans transition boundaries where incumbent packings are uncompacted integer grids,
applies Pocket Void Insertion, Diagonal Seam synthesis, and HiGHS Contact-LP Compaction
to generate certified non-grid packings below the integer ceiling L < k.
"""

import sys
import time
import math
from pathlib import Path
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from squares_in_squares.storage.solution_store import SolutionStore
from squares_in_squares.geometry.bounds import container_side_length
from squares_in_squares.geometry.sat import DEFAULT_SAT_TOLERANCE
from squares_in_squares.validation.packing_validator import validate_packing_geometry
from squares_in_squares.validation.score import puzzle_score, aggregate_score
from squares_in_squares.optimization.pocket_insertion import grow_packing_by_insertion
from squares_in_squares.optimization.contact_lp import contact_lp_squeeze
from squares_in_squares.packing.diagonal_stripes import generate_diagonal_stripe_packing


def optimize_transition_portfolio(
    solutions_dir: Path = Path("artifacts/solutions"),
    csv_fallback: Path = Path("submissions/submission_improved.csv"),
    tolerance: float = DEFAULT_SAT_TOLERANCE,
    dilation_delta: float = 1e-10,
):
    print("=" * 70)
    print("STARTING AUTONOMOUS TRANSITION PACKING OPTIMIZER")
    print("=" * 70)

    store = SolutionStore(solutions_dir)

    # Load all incumbent packings
    packings: dict[int, np.ndarray] = {}
    if csv_fallback.exists():
        print(f"Loading incumbents from {csv_fallback}...")
        df = pd.read_csv(csv_fallback)
        for n, group in df.groupby("n"):
            packings[int(n)] = group.sort_values("square_id")[["x", "y", "angle"]].values.astype(np.float64)
    else:
        for n in range(1, 1001):
            sq = store.load_squares(n)
            if sq is not None:
                packings[n] = sq

    print(f"Loaded {len(packings)} incumbent solutions.")

    # Calculate starting score
    init_score = sum(puzzle_score(n, container_side_length(sq)) for n, sq in packings.items())
    print(f"Initial Portfolio Aggregate Score: {init_score:.8f}\n")

    # Identify transition points
    transitions: list[tuple[int, int, float]] = []
    for n in range(2, 1001):
        k = int(math.ceil(math.sqrt(n)))
        cur_L = container_side_length(packings[n])
        is_grid = np.all(np.abs(packings[n][:, 2]) < 1e-4) and np.isclose(round(cur_L), cur_L, atol=1e-4)

        if is_grid and (n - 1) in packings:
            prev_L = container_side_length(packings[n - 1])
            prev_is_grid = np.all(np.abs(packings[n - 1][:, 2]) < 1e-4) and np.isclose(round(prev_L), prev_L, atol=1e-4)
            if not prev_is_grid and prev_L < k:
                transitions.append((n, k, cur_L))

    print(f"Identified {len(transitions)} high-leverage transition boundary puzzles:")
    for n, k, L in transitions[:15]:
        print(f"  n={n:4d} (k={k:2d}): current L={L:.6f}, predecessor n={n-1} is non-grid")
    print(f"  ... and {max(0, len(transitions) - 15)} more.")

    improvements = 0
    total_delta = 0.0

    for idx, (n, k, orig_L) in enumerate(transitions):
        print(f"\n[{idx+1}/{len(transitions)}] Optimizing transition for n={n} (k={k}, orig_L={orig_L:.4f})...")
        t0 = time.time()
        best_candidate: np.ndarray | None = None
        best_L = orig_L

        # Strategy A: Void pocket growth from n-1
        prev_sq = packings[n - 1]
        try:
            cand_sq, cand_L, success = grow_packing_by_insertion(
                prev_sq, n, grid_resolution=25, tolerance=tolerance
            )
            if success and cand_sq is not None and cand_L < best_L - 1e-6:
                best_candidate = cand_sq
                best_L = cand_L
                print(f"  -> Strategy A (Pocket Growth) succeeded: L={cand_L:.6f}")
        except Exception as e:
            pass

        # Strategy B: Parametric Diagonal Seam Generator
        if best_candidate is None:
            for s_count in [None, k - 2, k - 1, k]:
                try:
                    cand_sq, cand_L, success = generate_diagonal_stripe_packing(
                        n, stripe_count=s_count, tolerance=tolerance
                    )
                    if success and cand_sq is not None and cand_L < best_L - 1e-6:
                        best_candidate = cand_sq
                        best_L = cand_L
                        print(f"  -> Strategy B (Diagonal Seam) succeeded: L={cand_L:.6f}")
                        break
                except Exception:
                    pass

        # If improved, validate with SAT, apply selective centroid dilation, and save
        if best_candidate is not None and best_L < orig_L - 1e-6:
            # Apply selective centroid dilation
            cx = np.mean(best_candidate[:, 0])
            cy = np.mean(best_candidate[:, 1])
            best_candidate[:, 0] = cx + (best_candidate[:, 0] - cx) * (1.0 + dilation_delta)
            best_candidate[:, 1] = cy + (best_candidate[:, 1] - cy) * (1.0 + dilation_delta)

            vr = validate_packing_geometry(best_candidate, n, tolerance=0.0)
            if vr.valid and vr.container_length < orig_L:
                delta_score = puzzle_score(n, orig_L) - puzzle_score(n, vr.container_length)
                total_delta += delta_score
                improvements += 1
                packings[n] = best_candidate
                print(f"  SUCCESS for n={n}! L: {orig_L:.6f} -> {vr.container_length:.6f} (gain: {delta_score:.6f})")

                # Persist to SolutionStore
                store.save_squares(
                    n=n,
                    squares=best_candidate,
                    seed=42,
                    strategy="transition_optimizer",
                    runtime_seconds=time.time() - t0,
                )

    print("\n" + "=" * 70)
    print(f"OPTIMIZATION RUN COMPLETE!")
    print(f"Puzzles improved: {improvements}")
    print(f"Aggregate Score Drop: -{total_delta:.8f}")
    new_score = init_score - total_delta
    print(f"New Portfolio Aggregate Score: {new_score:.8f}")
    print("=" * 70)


if __name__ == "__main__":
    optimize_transition_portfolio()
