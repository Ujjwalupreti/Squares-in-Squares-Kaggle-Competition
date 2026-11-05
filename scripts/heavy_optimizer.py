"""Autonomous Multi-Core Heavy Packing Optimizer (Option A).

Runs parallelized centripetal contraction, soft-body contact relaxation,
rotational micro-annealing, and HiGHS convex LP compaction across
high-slack and transition puzzles to continuously compress container sizes
toward the 22.185898 milestone.
"""

from __future__ import annotations

import sys
import time
import math
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from squares_in_squares.storage.solution_store import SolutionStore
from squares_in_squares.geometry.bounds import container_side_length
from squares_in_squares.geometry.sat import squares_overlap, DEFAULT_SAT_TOLERANCE
from squares_in_squares.validation.packing_validator import validate_packing_geometry
from squares_in_squares.validation.score import puzzle_score
from squares_in_squares.optimization.contact_lp import contact_lp_squeeze


def optimize_single_puzzle(
    n: int,
    initial_squares: np.ndarray,
    max_trials: int = 25,
    max_steps_per_trial: int = 150,
    seed: int = 42,
    dilation_delta: float = 1e-10,
) -> tuple[int, np.ndarray, float, float, bool]:
    """Worker function to optimize a single puzzle using multi-strategy relaxation.

    Returns:
        (n, best_squares, orig_L, new_L, improved)
    """
    np.random.seed(seed + n)
    orig_L = container_side_length(initial_squares)
    best_L = orig_L
    best_squares = initial_squares.copy()

    angles = initial_squares[:, 2]
    c = np.abs(np.cos(angles))
    s = np.abs(np.sin(angles))
    hx = 0.5 * (c + s)
    hy = 0.5 * (s + c)

    cx = np.mean(initial_squares[:, 0])
    cy = np.mean(initial_squares[:, 1])

    for trial in range(max_trials):
        cand = initial_squares.copy()

        # Adaptive shrink rate (0.05% to 1.5%)
        shrink_rate = 0.0005 * (trial + 1)
        cand[:, 0] = cx + (cand[:, 0] - cx) * (1.0 - shrink_rate)
        cand[:, 1] = cy + (cand[:, 1] - cy) * (1.0 - shrink_rate)

        # Micro-rotations on a targeted subset of interior squares
        if trial > 2:
            num_rot = max(1, min(5, n // 10))
            rot_indices = np.random.choice(n, size=num_rot, replace=False)
            cand[rot_indices, 2] += np.random.uniform(-0.015, 0.015, size=num_rot)

        # Soft-body contact repulsion
        for step in range(max_steps_per_trial):
            grad_x = np.zeros(n, dtype=np.float64)
            grad_y = np.zeros(n, dtype=np.float64)
            ov_count = 0

            for i in range(n):
                for j in range(i + 1, n):
                    dx = cand[j, 0] - cand[i, 0]
                    dy = cand[j, 1] - cand[i, 1]
                    if abs(dx) >= hx[i] + hx[j] or abs(dy) >= hy[i] + hy[j]:
                        continue

                    if squares_overlap(
                        cand[i, 0], cand[i, 1], cand[i, 2],
                        cand[j, 0], cand[j, 1], cand[j, 2],
                        tolerance=1e-5,
                    ):
                        ov_count += 1
                        dist = math.hypot(dx, dy)
                        fx = (dx / dist) * 0.05 if dist > 1e-6 else np.random.uniform(-0.01, 0.01)
                        fy = (dy / dist) * 0.05 if dist > 1e-6 else np.random.uniform(-0.01, 0.01)
                        grad_x[i] -= fx
                        grad_x[j] += fx
                        grad_y[i] -= fy
                        grad_y[j] += fy

            if ov_count == 0:
                break

            decay = 1.0 - (step / max_steps_per_trial) * 0.5
            cand[:, 0] += grad_x * 0.05 * decay
            cand[:, 1] += grad_y * 0.05 * decay

        # Convex LP Compaction via HiGHS
        squeezed, sq_L, ok = contact_lp_squeeze(
            cand, n, contact_threshold=0.15, safety_margin=1e-10
        )

        if ok and sq_L < best_L - 1e-6:
            # Apply selective centroid dilation
            cx_cand = np.mean(squeezed[:, 0])
            cy_cand = np.mean(squeezed[:, 1])
            squeezed[:, 0] = cx_cand + (squeezed[:, 0] - cx_cand) * (1.0 + dilation_delta)
            squeezed[:, 1] = cy_cand + (squeezed[:, 1] - cy_cand) * (1.0 + dilation_delta)

            # Strict SAT verification at tolerance 0.0
            vr = validate_packing_geometry(squeezed, n, tolerance=0.0)
            if vr.valid and vr.container_length < best_L:
                best_L = vr.container_length
                best_squares = squeezed

    improved = best_L < orig_L - 1e-6
    return n, best_squares, orig_L, best_L, improved


def run_heavy_optimization(
    solutions_dir: Path = Path("artifacts/solutions"),
    csv_path: Path = Path("submissions/submission_improved.csv"),
    max_workers: int | None = None,
    target_count: int = 50,
):
    print("=" * 70)
    print("STARTING AUTONOMOUS MULTI-CORE HEAVY PACKING OPTIMIZER (OPTION A)")
    print("=" * 70)

    if max_workers is None:
        max_workers = min(4, os.cpu_count() or 4)

    store = SolutionStore(solutions_dir)

    # Load incumbents from primary submission
    print(f"Loading base portfolio from {csv_path}...")
    df = pd.read_csv(csv_path)
    packings: dict[int, np.ndarray] = {}
    for n, group in df.groupby("n"):
        packings[int(n)] = group.sort_values("square_id")[["x", "y", "angle"]].values.astype(np.float64)

    total_init_score = sum(puzzle_score(n, container_side_length(sq)) for n, sq in packings.items())
    print(f"Loaded {len(packings)} puzzles. Current Aggregate Score: {total_init_score:.8f}")

    # Prioritize puzzles by potential slack (L - sqrt(n))
    opportunities = []
    for n, sq in packings.items():
        L = container_side_length(sq)
        sqn = math.sqrt(n)
        slack = L - sqn
        score_val = (L / sqn) - 1.0
        # Exclude perfect squares n=k^2
        if round(sqn)**2 != n and slack > 0.40:
            opportunities.append((n, slack, score_val, sq))

    opportunities.sort(key=lambda x: x[1], reverse=True)
    selected_targets = opportunities[:target_count]

    print(f"\nDispatched {len(selected_targets)} high-slack puzzles across {max_workers} worker processes.")
    print("Top targeted puzzles:", [x[0] for x in selected_targets[:15]])

    total_gain = 0.0
    improvements_count = 0
    start_time = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(optimize_single_puzzle, n, sq): n
            for n, slack, sc, sq in selected_targets
        }

        for idx, future in enumerate(as_completed(futures)):
            n_val = futures[future]
            try:
                n, best_sq, orig_L, new_L, improved = future.result()
                elapsed = time.time() - start_time
                if improved:
                    gain = puzzle_score(n, orig_L) - puzzle_score(n, new_L)
                    total_gain += gain
                    improvements_count += 1
                    packings[n] = best_sq
                    # Save to SolutionStore
                    store.save_squares(
                        n=n,
                        squares=best_sq,
                        seed=42,
                        strategy="heavy_optimizer",
                        runtime_seconds=elapsed,
                    )
                    print(f"[{idx+1}/{len(selected_targets)}] *** BREAKTHROUGH on n={n:4d}! L: {orig_L:.6f} -> {new_L:.6f} (gain: {gain:.6f}) ***")
                else:
                    print(f"[{idx+1}/{len(selected_targets)}] n={n_val:4d} evaluated (no feasible reduction in budget).")
            except Exception as e:
                print(f"[{idx+1}/{len(selected_targets)}] Error optimizing n={n_val}: {e}")

    # Final summary and auto-rebuild
    print("\n" + "=" * 70)
    print("HEAVY OPTIMIZATION BATCH COMPLETED!")
    print(f"Total Puzzles Improved: {improvements_count}")
    print(f"Total Score Drop: -{total_gain:.8f}")
    final_score = total_init_score - total_gain
    print(f"Final Aggregate Competition Score: {final_score:.8f}")
    print("=" * 70)

    if improvements_count > 0:
        print("\nRebuilding updated submission CSVs...")
        records = []
        row_id = 0
        for n in range(1, 1001):
            sq = packings[n]
            for sq_id in range(n):
                records.append({
                    "id": row_id,
                    "n": n,
                    "square_id": sq_id,
                    "x": float(sq[sq_id, 0]),
                    "y": float(sq[sq_id, 1]),
                    "angle": float(sq[sq_id, 2]),
                })
                row_id += 1
        new_df = pd.DataFrame(records)
        new_df.to_csv(csv_path, index=False)
        new_df.to_csv("submissions/submission.csv", index=False)
        print("Updated submissions/submission_improved.csv and submissions/submission.csv successfully!")


if __name__ == "__main__":
    run_heavy_optimization()
