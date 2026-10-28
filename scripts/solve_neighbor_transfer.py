#!/usr/bin/env python
"""Automated Neighbor-Transfer & Squeeze Solver for Transition Puzzles.

Transfers packing configurations from puzzle n-1 to puzzle n, finds the best
pocket to insert the n-th square, relaxes overlaps, and squeezes using HiGHS LP.
Strictly validates zero-overlap under 0.0 tolerance before updating SolutionStore.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

# Ensure src is in sys.path
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from squares_in_squares.config import Config
from squares_in_squares.storage.solution_store import SolutionStore, SolutionRecord
from squares_in_squares.geometry.bounds import container_side_length, half_extents
from squares_in_squares.geometry.sat import squares_overlap, DEFAULT_SAT_TOLERANCE
from squares_in_squares.validation.packing_validator import validate_packing_geometry


def get_separating_axis_constraint(xi, yi, thi, xj, yj, thj):
    """Compute the separating axis normal and required gap between square i and square j."""
    ci, si = math.cos(thi), math.sin(thi)
    cj, sj = math.cos(thj), math.sin(thj)
    dx = xj - xi
    dy = yj - yi

    cos_diff = ci * cj + si * sj
    sin_diff = si * cj - ci * sj
    wj1 = 0.5 * (abs(cos_diff) + abs(sin_diff))

    proj1 = dx * ci + dy * si
    req1 = 0.5 + wj1
    g1 = abs(proj1) - req1

    proj2 = -dx * si + dy * ci
    req2 = 0.5 + wj1
    g2 = abs(proj2) - req2

    proj3 = dx * cj + dy * sj
    req3 = wj1 + 0.5
    g3 = abs(proj3) - req3

    proj4 = -dx * sj + dy * cj
    req4 = wj1 + 0.5
    g4 = abs(proj4) - req4

    candidates = [
        (g1, ci if proj1 >= 0 else -ci, si if proj1 >= 0 else -si, req1),
        (g2, -si if proj2 >= 0 else si, ci if proj2 >= 0 else -ci, req2),
        (g3, cj if proj3 >= 0 else -cj, sj if proj3 >= 0 else -sj, req3),
        (g4, -sj if proj4 >= 0 else sj, cj if proj4 >= 0 else -cj, req4),
    ]
    best_cand = max(candidates, key=lambda c: c[0])
    return best_cand[1], best_cand[2], best_cand[3]


def highs_squeeze(squares: np.ndarray, n: int, safety_margin: float = 1e-8) -> tuple[np.ndarray, float]:
    """Formulate and solve a HiGHS LP to squeeze L with fixed angles."""
    orig_L = container_side_length(squares)
    h = half_extents(squares[:, 2])
    num_vars = 1 + 2 * n

    c_obj = np.zeros(num_vars)
    c_obj[0] = 1.0

    A_rows = []
    b_rows = []

    # Container boundary constraints
    for i in range(n):
        xi_var = 1 + i
        yi_var = 1 + n + i
        # x_i >= h_i => -x_i <= -h_i
        r = np.zeros(num_vars); r[xi_var] = -1.0; A_rows.append(r); b_rows.append(-h[i])
        # x_i + h_i <= L => x_i - L <= -h_i
        r = np.zeros(num_vars); r[xi_var] = 1.0; r[0] = -1.0; A_rows.append(r); b_rows.append(-h[i])
        # y_i >= h_i => -y_i <= -h_i
        r = np.zeros(num_vars); r[yi_var] = -1.0; A_rows.append(r); b_rows.append(-h[i])
        # y_i + h_i <= L => y_i - L <= -h_i
        r = np.zeros(num_vars); r[yi_var] = 1.0; r[0] = -1.0; A_rows.append(r); b_rows.append(-h[i])

    x = squares[:, 0]
    y = squares[:, 1]
    angles = squares[:, 2]

    # Local bounds on movement to preserve topology
    bounds = [(1.0, orig_L + 1.0)]
    for i in range(n):
        bounds.append((max(h[i], x[i] - 0.25), min(orig_L - h[i], x[i] + 0.25)))
    for i in range(n):
        bounds.append((max(h[i], y[i] - 0.25), min(orig_L - h[i], y[i] + 0.25)))

    # Separating axis constraints
    for i in range(n):
        for j in range(i + 1, n):
            if abs(x[j] - x[i]) >= h[i] + h[j] + 0.3:
                continue
            if abs(y[j] - y[i]) >= h[i] + h[j] + 0.3:
                continue
            ax, ay, req = get_separating_axis_constraint(x[i], y[i], angles[i], x[j], y[j], angles[j])
            xi_var = 1 + i; xj_var = 1 + j
            yi_var = 1 + n + i; yj_var = 1 + n + j
            r = np.zeros(num_vars)
            r[xi_var] = ax; r[xj_var] = -ax
            r[yi_var] = ay; r[yj_var] = -ay
            A_rows.append(r)
            b_rows.append(-req - safety_margin)

    A_ub = np.array(A_rows)
    b_ub = np.array(b_rows)

    res = linprog(c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    if res.success and res.fun < orig_L:
        new_L = float(res.fun)
        new_x = res.x[1:1+n]
        new_y = res.x[1+n:1+2*n]
        new_squares = np.column_stack([new_x, new_y, angles])
        return new_squares, new_L
    return squares, orig_L


def find_best_insertion_site(
    base_squares: np.ndarray,
    target_L: float,
    angles_to_try: list[float] | None = None,
    grid_res: int = 50,
) -> tuple[float, float, float]:
    """Scan the container to find coordinates (x, y, theta) with minimal penetration."""
    if angles_to_try is None:
        angles_to_try = [0.0, math.pi / 4.0, math.radians(24.0), math.radians(71.0)]

    h_arr = half_extents(base_squares[:, 2])
    n_base = len(base_squares)

    xs = np.linspace(0.6, target_L - 0.6, grid_res)
    ys = np.linspace(0.6, target_L - 0.6, grid_res)

    best_site = (target_L / 2.0, target_L / 2.0, 0.0)
    min_penalty = float('inf')

    # Vectorized broadphase grid
    for th in angles_to_try:
        hc = 0.5 * (abs(math.cos(th)) + abs(math.sin(th)))
        for x in xs:
            if x - hc < 0 or x + hc > target_L:
                continue
            # AABB filter along X
            dx_arr = np.abs(base_squares[:, 0] - x)
            x_cand_mask = dx_arr < (h_arr + hc + 0.1)
            if not np.any(x_cand_mask):
                # Completely empty X slice
                return x, ys[0], th

            cand_indices = np.where(x_cand_mask)[0]

            for y in ys:
                if y - hc < 0 or y + hc > target_L:
                    continue

                penalty = 0.0
                for idx in cand_indices:
                    dy = abs(base_squares[idx, 1] - y)
                    req_dist = h_arr[idx] + hc
                    if dy >= req_dist:
                        continue
                    dist = math.hypot(dx_arr[idx], dy)
                    if dist < req_dist:
                        if squares_overlap(x, y, th, base_squares[idx, 0], base_squares[idx, 1], base_squares[idx, 2], tolerance=1e-5):
                            penalty += max(0.01, req_dist - dist)

                if penalty < min_penalty:
                    min_penalty = penalty
                    best_site = (x, y, th)
                    if penalty == 0.0:
                        return best_site

    return best_site


def solve_neighbor_transfer_puzzle(
    n: int,
    store: SolutionStore,
    max_steps: int = 1500,
    lr: float = 0.015,
) -> bool:
    """Solve puzzle n using neighbor transfer from n-1, relax, squeeze, and save if improved."""
    print(f"\n==================================================")
    print(f"  Attempting Neighbor-Transfer for Puzzle n = {n}")
    print(f"==================================================")

    # 1. Load incumbent for n
    rec_n = store.load(n)
    grid_L = float(math.ceil(math.sqrt(n)))
    current_L = rec_n.container_length if rec_n else grid_L
    current_score = rec_n.score if rec_n else (grid_L / math.sqrt(n) - 1.0)
    print(f"Current Incumbent: L = {current_L:.8f}, score = {current_score:.8f}")

    # 2. Load solution for n - 1
    sq_prev = store.load_squares(n - 1)
    if sq_prev is None:
        print(f"Error: No existing solution for n-1 ({n-1}). Cannot transfer.")
        return False

    prev_L = container_side_length(sq_prev)
    print(f"Seeding from n-1 ({n-1}): L = {prev_L:.8f}")

    # If prev_L is already >= grid_L, transfer won't beat the integer grid
    target_L = min(grid_L - 1e-4, max(prev_L, grid_L - 0.2))

    # 3. Find best insertion site for n-th square
    print(f"Scanning for insertion site inside L_target = {target_L:.4f}...")
    best_x, best_y, best_th = find_best_insertion_site(sq_prev, target_L=target_L)
    print(f"Best insertion found: x={best_x:.4f}, y={best_y:.4f}, angle={best_th:.4f} rad")

    # Assemble candidate
    candidate = np.vstack([sq_prev, [[best_x, best_y, best_th]]])
    n_curr = len(candidate)

    # 4. Soft-body repulsive relaxation to resolve local penetration
    print("Running repulsive coordinate relaxation...")
    h = half_extents(candidate[:, 2])
    best_valid = None
    best_L = current_L

    for step in range(max_steps):
        grad = np.zeros((n_curr, 2))
        h = half_extents(candidate[:, 2])

        # Boundary penalty
        for i in range(n_curr):
            if candidate[i, 0] - h[i] < 0:
                grad[i, 0] -= (candidate[i, 0] - h[i]) * 15.0
            if candidate[i, 0] + h[i] > target_L:
                grad[i, 0] -= (candidate[i, 0] + h[i] - target_L) * 15.0
            if candidate[i, 1] - h[i] < 0:
                grad[i, 1] -= (candidate[i, 1] - h[i]) * 15.0
            if candidate[i, 1] + h[i] > target_L:
                grad[i, 1] -= (candidate[i, 1] + h[i] - target_L) * 15.0

        # Pairwise overlap forces (pruned by AABB)
        ov_count = 0
        for i in range(n_curr):
            for j in range(i + 1, n_curr):
                dx = candidate[j, 0] - candidate[i, 0]
                dy = candidate[j, 1] - candidate[i, 1]
                req = h[i] + h[j]
                if abs(dx) >= req or abs(dy) >= req:
                    continue
                dist = math.hypot(dx, dy)
                if dist < 1e-5:
                    dx = 1e-3; dy = 1e-3; dist = 1e-3

                if squares_overlap(candidate[i, 0], candidate[i, 1], candidate[i, 2],
                                   candidate[j, 0], candidate[j, 1], candidate[j, 2],
                                   tolerance=1e-7):
                    ov_count += 1
                    penetration = req - dist
                    f = (penetration + 0.05) * 8.0
                    grad[j, 0] += (dx / dist) * f
                    grad[j, 1] += (dy / dist) * f
                    grad[i, 0] -= (dx / dist) * f
                    grad[i, 1] -= (dy / dist) * f

        if ov_count == 0:
            vr = validate_packing_geometry(candidate, n, tolerance=0.0)
            if vr.valid and vr.container_length < best_L:
                print(f"Step {step}: Found certified zero-overlap packing! L = {vr.container_length:.8f}")
                best_valid = candidate.copy()
                best_L = vr.container_length
                break

        candidate[:, :2] += lr * grad
        for i in range(n_curr):
            candidate[i, 0] = np.clip(candidate[i, 0], h[i], target_L - h[i])
            candidate[i, 1] = np.clip(candidate[i, 1], h[i], target_L - h[i])

        if step % 300 == 0 and step > 0:
            print(f"  Step {step:4d}: active overlaps = {ov_count}")

    # 5. If valid packing found, run HiGHS LP squeeze
    if best_valid is not None:
        print("Applying HiGHS Linear Programming squeeze...")
        squeezed_sq, squeezed_L = highs_squeeze(best_valid, n)
        vr_fin = validate_packing_geometry(squeezed_sq, n, tolerance=0.0)

        final_sq = squeezed_sq if vr_fin.valid else best_valid
        final_L = vr_fin.container_length if vr_fin.valid else best_L
        final_score = final_L / math.sqrt(n) - 1.0

        if final_L < current_L - 1e-6:
            score_gain = current_score - final_score
            print(f"\n SUCCESS! Improved puzzle n={n}!")
            print(f"  Old L: {current_L:.8f} -> New L: {final_L:.8f}")
            print(f"  Score Reduction: {score_gain:.8f}")

            # Save to SolutionStore
            record = SolutionRecord(
                n=n,
                squares=[[float(c) for c in row] for row in final_sq],
                container_length=float(final_L),
                score=float(final_score),
                seed=42,
                strategy="neighbor_transfer_squeeze",
                runtime_seconds=0.0,
            )
            store.save(record)
            return True
        else:
            print(f"Valid packing found but L ({final_L:.8f}) not strictly better than incumbent ({current_L:.8f}).")
            return False
    else:
        print(f"Relaxation did not resolve all overlaps within {max_steps} steps.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Neighbor-Transfer solver for transition puzzles.")
    parser.add_argument("--targets", nargs="+", type=int, default=[184, 212, 242],
                        help="List of puzzle sizes n to solve.")
    args = parser.parse_args()

    config = Config.default()
    store = SolutionStore(config.solutions_dir)

    print(f"Running Neighbor-Transfer Solver on targets: {args.targets}")
    improved = []
    for n in args.targets:
        ok = solve_neighbor_transfer_puzzle(n, store)
        if ok:
            improved.append(n)

    print("\n==================================================")
    print(f"Summary: Successfully improved {len(improved)} / {len(args.targets)} puzzles: {improved}")
    print("==================================================")


if __name__ == "__main__":
    main()
