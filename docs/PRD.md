# Product Requirements Document (PRD)
## Project: Squares in Squares — Competitive Packing Optimizer

**Status:** Initial specification  
**Language:** Python  
**Target platform:** Kaggle Notebooks / CPU-first  
**Competition scope:** Puzzles `n = 1..1000`

## 1. Product vision
Build a reproducible optimization system that generates non-overlapping packings of `n` unit squares inside the smallest practical axis-aligned square container, improving the aggregate competition score across up to 1,000 puzzles.

## 2. Problem statement
For each puzzle size `n`, produce exactly `n` unit squares. Each square is represented by its center `(x, y)` and rotation angle `angle` in radians. Square interiors must not overlap. The enclosing container is axis-aligned, and its side length `L` is derived from the submitted geometry.

Per-puzzle score:
`score(n) = L / sqrt(n) - 1`

Lower is better. The aggregate objective is the sum of the scores for the puzzles evaluated by the competition.

## 3. Users and use cases
- Competition participant developing a competitive solution.
- Researcher experimenting with geometric packing and stochastic optimization.
- Developer reproducing experiments across Kaggle sessions and GitHub commits.

Primary use cases:
1. Generate a valid baseline for every puzzle.
2. Optimize a selected range of puzzle sizes.
3. Validate a candidate packing independently.
4. Save and resume long-running experiments.
5. Build and audit a submission CSV in the required schema.

## 4. Functional requirements
### FR-1: Puzzle management
- Support `1 <= n <= 1000`.
- Support configurable puzzle ranges, random seeds, iteration limits, and restart counts.
- Run a small subset before full-scale optimization.

### FR-2: Candidate generation
- Generate at least one feasible baseline packing for every supported `n`.
- Support multiple initial layouts as the project evolves: grid, staggered, rotated patterns, and stored incumbents.
- Never assume an initial candidate is valid without validation.

### FR-3: Geometry engine
- Represent each square as `(x, y, angle)`.
- Compute square vertices and axis-aligned extents.
- Compute enclosing side length.
- Detect interior overlap with the Separating Axis Theorem (SAT), permitting edge/corner contact subject to a carefully tested numerical tolerance.

### FR-4: Optimization
- Provide a baseline solver and a configurable optimization solver.
- Support local translation and rotation moves, restarts, and simulated annealing or other documented strategies.
- Keep the best independently validated feasible solution separately from the current search state.
- Accept candidate solutions only according to documented acceptance and feasibility policies.

### FR-5: Persistence
- Store the best valid packing per `n`, its score, seed, strategy, runtime, and metadata.
- Support checkpoint/restart without losing the incumbent.
- Reject malformed or incompatible checkpoint data safely.

### FR-6: Validation
- Validate finite coordinates and angles.
- Check expected square count and pairwise non-overlap.
- Recompute container side length and score independently.
- Validate the complete submission structure and row counts.

### FR-7: Submission
- Export columns exactly: `id,n,square_id,x,y,angle`.
- Use unique sequential integer `id` values.
- For each `n`, include square IDs `0..n-1`.
- Support partial submissions during development and a complete submission of all 1,000 puzzles.

### FR-8: Experiment tracking
- Record puzzle size, seed, strategy, initial/best length, score, iteration count, runtime, validity, and code/config version.
- Compare every optimization experiment against the same baseline.

## 5. Non-functional requirements
- **Correctness:** independently validate all solutions before they enter the final solution store.
- **Reproducibility:** fixed seeds and saved configuration for each run.
- **Recoverability:** interrupted runs can resume from checkpoints.
- **Performance:** use spatial filtering or incremental checks where naive all-pairs checking becomes too expensive.
- **Maintainability:** separate geometry, packing, optimization, validation, storage, and submission code.
- **Portability:** CPU-first; no GPU requirement for geometric calculations.
- **Auditability:** keep logs and document objective/validator versions.

## 6. MVP scope
Included:
- Geometry primitives and bounding calculations.
- SAT collision detection.
- Grid baseline.
- Independent packing validator.
- Score calculator.
- CSV builder and submission audit.
- Small-case unit and integration tests.

Deferred until the MVP passes:
- Advanced multi-start annealing.
- Sophisticated collective moves.
- Adaptive puzzle difficulty scheduling.
- High-performance compiled collision kernels.
- Automated hyperparameter tuning.

## 7. Out of scope
- Guaranteeing mathematically optimal solutions for every `n`.
- Proving optimality for open packing problems.
- GPU-based machine learning approaches unless experiments show a clear benefit.
- Changing competition rules or evaluation logic.

## 8. Success criteria
1. Baseline generator creates one valid packing for each `n=1..1000`.
2. Complete output has `500,500` rows.
3. All row IDs are unique and sequential.
4. Each puzzle has exactly `n` squares with IDs `0..n-1`.
5. All coordinates and angles are finite.
6. Independent validation reports no overlapping interiors.
7. Container lengths and aggregate score are recomputed after CSV reload.
8. Optimization improves aggregate score versus baseline without introducing invalid solutions.
9. Interrupted experiments can resume without losing the best feasible incumbent.

## 9. Risks and mitigations
- **Floating-point tolerance errors:** test touching and near-touching cases; separate optimizer penalties from final validator.
- **Quadratic collision checks:** introduce bounding-box/spatial-grid candidate filtering.
- **Kaggle session interruption:** checkpoint frequently and export artifacts to persistent storage.
- **Unreproducible results:** record seeds, config, and code version.
- **False confidence in score:** compare local scoring with the official competition metric notebook before final submission.
