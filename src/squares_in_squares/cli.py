"""Command-line interface for Squares in Squares optimizer.

Provides subcommands:
- baseline: Generate and store baseline packings
- optimize: Run optimization on a range of puzzle sizes
- benchmark: Run controlled benchmark comparing baseline vs optimization
- validate: Independently validate solutions in the store
- submit: Build a submission CSV from stored solutions
- audit: Independently audit a submission CSV
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .config import Config
from .packing.grid import grid_packing
from .validation.packing_validator import validate_packing_geometry
from .validation.submission_validator import audit_submission
from .submission.build_submission import build_submission
from .storage.solution_store import SolutionStore, SolutionRecord
from .optimization.solver import solve_puzzle
from .experiments.benchmark import run_benchmark


def cmd_baseline(args: argparse.Namespace) -> int:
    """Generate and store baseline grid solutions."""
    config = Config.from_yaml(args.config) if args.config else Config.default()
    config.ensure_dirs()
    store = SolutionStore(config.solutions_dir)

    n_min = args.n_min or config.n_min
    n_max = args.n_max or config.n_max

    print(f"Generating baseline packings for n={n_min}..{n_max}...")
    start_time = time.time()
    valid_count = 0
    total_score = 0.0

    for n in range(n_min, n_max + 1):
        squares = grid_packing(n)
        vr = validate_packing_geometry(squares, n, tolerance=config.sat_tolerance)
        if not vr.valid:
            print(f"ERROR: Baseline for n={n} failed validation: {vr.errors}")
            return 1

        record = SolutionRecord(
            n=n,
            squares=squares.tolist(),
            container_length=vr.container_length,
            score=vr.score,
            seed=0,
            strategy="grid",
            runtime_seconds=0.0,
        )
        store.save(record)
        valid_count += 1
        total_score += vr.score

        if n % 100 == 0 or n == n_max:
            print(f"  Processed n={n}/{n_max} (accumulated score: {total_score:.4f})")

    elapsed = time.time() - start_time
    print(f"Baseline generation complete in {elapsed:.2f}s:")
    print(f"  Puzzles generated: {valid_count}/{n_max - n_min + 1}")
    print(f"  Aggregate score:   {total_score:.6f}")
    return 0


def cmd_optimize(args: argparse.Namespace) -> int:
    """Run optimization on puzzle range."""
    config = Config.from_yaml(args.config) if args.config else Config.default()
    config.ensure_dirs()
    store = SolutionStore(config.solutions_dir)

    n_min = args.n_min or config.n_min
    n_max = args.n_max or config.n_max

    print(f"Running optimization for n={n_min}..{n_max}...")
    for n in range(n_min, n_max + 1):
        existing = store.load(n)
        incumbent_score = existing.score if existing else float("inf")

        res = solve_puzzle(n, config=config, use_optimization=True)
        print(
            f"n={n:4d}: baseline_score={res.baseline_score:.4f}, "
            f"best_score={res.score:.4f}, strategy={res.strategy}, "
            f"runtime={res.runtime_seconds:.2f}s, valid={res.valid}"
        )

        if res.valid and res.score < incumbent_score and res.squares is not None:
            record = SolutionRecord(
                n=n,
                squares=res.squares.tolist(),
                container_length=res.container_length,
                score=res.score,
                seed=res.seed,
                strategy=res.strategy,
                runtime_seconds=res.runtime_seconds,
            )
            store.save(record)
            print(f"  -> Saved new best solution for n={n} (score={res.score:.6f})")

    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    """Run controlled benchmark."""
    config = Config.from_yaml(args.config) if args.config else Config.default()
    config.ensure_dirs()

    n_min = args.n_min or 2
    n_max = args.n_max or 30

    print(f"Running benchmark for n={n_min}..{n_max} (optimization={args.optimize})...")
    report = run_benchmark(
        n_min=n_min,
        n_max=n_max,
        config=config,
        use_optimization=args.optimize,
    )

    print("\n=== Benchmark Summary ===")
    print(f"Range:               n={report.n_range[0]}..{report.n_range[1]}")
    print(f"Total puzzles:       {report.total_puzzles}")
    print(f"Valid puzzles:       {report.valid_puzzles}")
    print(f"Baseline aggregate:  {report.baseline_aggregate:.6f}")
    print(f"Result aggregate:    {report.optimized_aggregate:.6f}")
    print(f"Improvement:         {report.improvement:.6f}")
    print(f"Total runtime:       {report.total_runtime:.2f}s")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Independently validate stored solutions."""
    config = Config.from_yaml(args.config) if args.config else Config.default()
    store = SolutionStore(config.solutions_dir)

    n_min = args.n_min or config.n_min
    n_max = args.n_max or config.n_max

    print(f"Validating solutions in store for n={n_min}..{n_max}...")
    errors = 0
    valid_count = 0
    total_score = 0.0

    for n in range(n_min, n_max + 1):
        squares = store.load_squares(n)
        if squares is None:
            print(f"Missing solution for n={n}")
            errors += 1
            continue

        vr = validate_packing_geometry(squares, n, tolerance=config.sat_tolerance)
        if not vr.valid:
            print(f"Validation FAILED for n={n}: {vr.errors}")
            errors += 1
        else:
            valid_count += 1
            total_score += vr.score

    print(f"\nValidation complete: {valid_count} valid, {errors} errors.")
    print(f"Aggregate score: {total_score:.6f}")
    return 0 if errors == 0 else 1


def cmd_submit(args: argparse.Namespace) -> int:
    """Build submission CSV from stored solutions."""
    config = Config.from_yaml(args.config) if args.config else Config.default()
    config.ensure_dirs()
    store = SolutionStore(config.solutions_dir)

    out_path = Path(args.output) if args.output else config.submissions_dir / "submission.csv"
    n_min = args.n_min or config.n_min
    n_max = args.n_max or config.n_max

    print(f"Building submission CSV at {out_path} for n={n_min}..{n_max}...")
    success, total_rows, missing = build_submission(
        store=store,
        output_path=out_path,
        n_min=n_min,
        n_max=n_max,
    )

    if not success:
        print(f"ERROR: Missing puzzles in solution store: {missing[:10]}...")
        return 1

    print(f"Submission written successfully: {total_rows} rows.")

    if args.audit:
        print("Running audit on generated CSV...")
        audit_res = audit_submission(out_path, n_min=n_min, n_max=n_max, tolerance=config.sat_tolerance)
        if audit_res.valid:
            print(f"AUDIT PASSED! Total rows: {audit_res.total_rows}, Aggregate score: {audit_res.aggregate_score:.6f}")
            return 0
        else:
            print(f"AUDIT FAILED! Errors: {audit_res.errors}")
            return 1

    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """Run independent audit on a submission CSV."""
    config = Config.from_yaml(args.config) if args.config else Config.default()
    csv_path = Path(args.csv)
    n_min = args.n_min or config.n_min
    n_max = args.n_max or config.n_max

    print(f"Auditing submission file: {csv_path} (n={n_min}..{n_max})...")
    res = audit_submission(csv_path, n_min=n_min, n_max=n_max, tolerance=config.sat_tolerance)

    if res.valid:
        print(f"AUDIT PASSED!")
        print(f"  Total rows:      {res.total_rows} (expected: {res.expected_rows})")
        print(f"  Unique puzzles:  {res.unique_puzzles}")
        print(f"  Aggregate score: {res.aggregate_score:.6f}")
        return 0
    else:
        print(f"AUDIT FAILED with {len(res.errors)} error(s):")
        for err in res.errors[:20]:
            print(f"  - {err}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    cfg_parent = argparse.ArgumentParser(add_help=False)
    cfg_parent.add_argument("--config", "-c", type=str, help="Path to YAML config file")

    parser = argparse.ArgumentParser(
        prog="squares-in-squares",
        description="Competitive packing optimizer for Kaggle Squares in Squares",
        parents=[cfg_parent],
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to run")

    # baseline
    p_base = subparsers.add_parser("baseline", parents=[cfg_parent], help="Generate and store baseline grid packings")
    p_base.add_argument("--n-min", type=int, help="Minimum puzzle size")
    p_base.add_argument("--n-max", type=int, help="Maximum puzzle size")
    p_base.set_defaults(func=cmd_baseline)

    # optimize
    p_opt = subparsers.add_parser("optimize", parents=[cfg_parent], help="Run optimization solver")
    p_opt.add_argument("--n-min", type=int, help="Minimum puzzle size")
    p_opt.add_argument("--n-max", type=int, help="Maximum puzzle size")
    p_opt.set_defaults(func=cmd_optimize)

    # benchmark
    p_bench = subparsers.add_parser("benchmark", parents=[cfg_parent], help="Run controlled benchmark")
    p_bench.add_argument("--n-min", type=int, default=2, help="Minimum puzzle size")
    p_bench.add_argument("--n-max", type=int, default=30, help="Maximum puzzle size")
    p_bench.add_argument("--optimize", action="store_true", help="Enable simulated annealing optimization")
    p_bench.set_defaults(func=cmd_benchmark)

    # validate
    p_val = subparsers.add_parser("validate", parents=[cfg_parent], help="Validate stored solutions")
    p_val.add_argument("--n-min", type=int, help="Minimum puzzle size")
    p_val.add_argument("--n-max", type=int, help="Maximum puzzle size")
    p_val.set_defaults(func=cmd_validate)

    # submit
    p_sub = subparsers.add_parser("submit", parents=[cfg_parent], help="Build submission CSV")
    p_sub.add_argument("--output", "-o", type=str, help="Output CSV path")
    p_sub.add_argument("--n-min", type=int, help="Minimum puzzle size")
    p_sub.add_argument("--n-max", type=int, help="Maximum puzzle size")
    p_sub.add_argument("--audit", action="store_true", help="Audit the CSV after writing")
    p_sub.set_defaults(func=cmd_submit)

    # audit
    p_audit = subparsers.add_parser("audit", parents=[cfg_parent], help="Audit an existing submission CSV")
    p_audit.add_argument("csv", type=str, help="Path to submission CSV")
    p_audit.add_argument("--n-min", type=int, help="Minimum puzzle size")
    p_audit.add_argument("--n-max", type=int, help="Maximum puzzle size")
    p_audit.set_defaults(func=cmd_audit)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
