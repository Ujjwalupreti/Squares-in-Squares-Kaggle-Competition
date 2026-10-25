# Squares in Squares — Competitive Optimization Project

A Python project for generating, optimizing, validating, and submitting packings of unit squares for the Kaggle **Squares in Squares** competition.

## Objective

For each puzzle size `n`, place exactly `n` non-overlapping unit squares inside an axis-aligned square container. Each unit square is represented by center coordinates `(x, y)` and a rotation angle in radians.

The competition's per-puzzle score is:

`score(n) = L / sqrt(n) - 1`

where `L` is the enclosing container side length. Lower is better. The project targets `n=1..1000`.

## Core strategy

1. Build and test a correct geometry engine.
2. Generate a feasible grid baseline for all puzzle sizes.
3. Validate independently with the Separating Axis Theorem.
4. Optimize with multi-start simulated annealing and local search.
5. Store the best valid incumbent and checkpoint long-running jobs.
6. Audit the generated CSV after writing and reloading it.

The project does not claim to prove globally optimal packings.

## Planned technology

- Python 3.10+
- NumPy
- pandas
- PyYAML
- pytest
- Optional: SciPy for spatial acceleration and Matplotlib for visualization

## Repository structure

```text
config/                     YAML configuration
notebooks/                  Exploratory Kaggle notebooks
src/squares_in_squares/
  geometry/                 Square transforms, bounds, SAT, spatial index
  packing/                  Initial layout strategies
  optimization/             Objective, moves, annealing, solver
  validation/               Independent packing and CSV validation
  storage/                  Checkpoints and solution store
  experiments/              Benchmarking and metrics
  submission/               CSV builder and final audit
scripts/                    Runnable entry points
tests/unit/                 Geometry and scoring tests
tests/integration/          Solver, checkpoint, and submission tests
artifacts/                  Local generated outputs (not normally committed)
submissions/                Final competition CSV
```

## Environment setup

Create a virtual environment, then install dependencies:

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

Install dependencies according to the actual project configuration. Keep versions pinned for reproducible competition runs.

## Development workflow

1. Read `PRD.md`, `ARCHITECTURE.md`, `DESIGN.md`, `RULES.md`, and `TASKS.md`.
2. Run geometry unit tests.
3. Generate baseline packings for small `n`.
4. Validate all baseline layouts.
5. Run optimization on a small, fixed benchmark.
6. Compare scores using equal compute budgets.
7. Scale to all 1,000 puzzles with checkpoints.
8. Revalidate saved solutions and audit the final CSV.

## Submission schema

Required columns in exact order:

`id,n,square_id,x,y,angle`

For a complete submission, the expected number of rows is:

`1 + 2 + ... + 1000 = 500,500`

Each puzzle `n` must contain exactly `n` rows and square IDs `0..n-1`. Partial submissions can be used during development if permitted by the current competition rules.

## Correctness requirements

- All values must be finite.
- Square interiors must not overlap.
- Edge and corner contact are allowed.
- Container bounds must account for square rotation.
- Validate independently after reloading saved solutions and the CSV.
- Never accept an overlap penalty as proof that a packing is valid.

## Kaggle and GitHub

Use GitHub for source control and Kaggle for computation. Clone the repository into a Kaggle notebook, run small tests first, and save checkpoints to persistent storage before the session ends. Notebook-to-GitHub linking does not automatically synchronize all project files; commit/push code changes separately when needed.

## Competition references

- Competition: https://www.kaggle.com/competitions/squares-in-squares
- Metric notebook: https://www.kaggle.com/code/metric/squares-in-squares

Before final submission, compare the local score implementation and CSV expectations with the current official competition metric and rules.

## Project status

This repository documentation specifies the planned architecture and implementation process. It does not imply that all solver modules have already been implemented. Track actual completion and test evidence in `TASKS.md`.
