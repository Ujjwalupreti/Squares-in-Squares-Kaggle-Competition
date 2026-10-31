# Technical and Experiment Design
## Squares in Squares

This document defines the project's internal design conventions, optimization experiment design, and output contracts. It is not a visual UI design document because the project is a geometry optimizer rather than a web application.

## 1. Design principles
- Correctness before optimization speed.
- Deterministic, explainable components.
- Search heuristics must not be trusted as validators.
- Small experiments before large runs.
- Preserve incumbents and compare scores consistently.
- Every optimization claim must be supported by logged measurements.

## 2. Core data representation
A square is a three-value record:
- `x`: center x-coordinate.
- `y`: center y-coordinate.
- `angle`: rotation in radians.

Use a NumPy array of shape `(n, 3)` internally when vectorized calculations are useful. Public module boundaries should document whether they accept arrays or Python sequences.

## 3. Coordinate and angle conventions
- Coordinates are continuous floating-point values.
- Angles are radians.
- Square side length is exactly `1`.
- Square centers define the geometry; corners are derived.
- The container is axis-aligned, even when squares are rotated.
- Translation of all squares by the same vector does not change score; optionally normalize a saved packing to a stable origin for easier comparison.

## 4. Bounds design
Use the exact half-extent formula for axis-aligned bounds. Avoid approximating a rotated square using only its center or unrotated side. Compute bounds from all squares, not just the last moved square, when independently validating.

## 5. Collision design
Use SAT with four candidate axes for two squares:
- Two local axes from square A.
- Two local axes from square B.

The broad phase may use bounding boxes to avoid unnecessary SAT checks. The narrow phase must use the actual oriented squares. Contact is allowed; the tolerance policy must avoid both false acceptance of meaningful overlaps and false rejection of contact.

### 5.1 Submission Gatekeeper & Kaggle `mpmath` Safeguard
- For external candidate ingestion (`scripts/ingest_solutions.py`), a strict zero-tolerance policy (`tolerance = 0.0`) is enforced.
- Kaggle evaluates submissions with multi-precision interval arithmetic (`mpmath`). To prevent floating-point rounding errors on tight algebraic contact configurations (such as $n=5$), an analytical positive clearance buffer ($\epsilon = 10^{-7}$) is applied:
  $$L_5 = 2.0 + \frac{1}{\sqrt{2}} + 10^{-7} \approx 2.7071068812$$
- This guarantees zero overlap under arbitrary-precision evaluation and prevents false disqualifications.

## 6. Objective design
Competition metric for each puzzle:
`score(n) = L / sqrt(n) - 1`

The score is scale-aware and appropriate for cross-puzzle comparison. During search, an objective may include an overlap penalty, but the final reported score must use `L` for a validated feasible packing only.

Track:
- initial container length
- best feasible container length
- normalized score
- aggregate score over the evaluated range
- validity status
- runtime and iteration count

## 7. Candidate moves
Initial move families:
1. Small translation of one square.
2. Rotation of one square.
3. Translation plus rotation.
4. Move a group of nearby squares.
5. Boundary-focused move for a square defining an extremum.
6. Restart from a different initial arrangement.

Move size should adapt to the search phase: broader early exploration and smaller late refinement. This is a hypothesis to benchmark, not an assumed improvement.

## 8. Experiment protocol
### Stage A: Geometry tests
Test known separated, touching, overlapping, and rotated square pairs. Compare SAT against a separate corner/projection reference for randomized pairs.

### Stage B: Baseline
Run grid packing for `n=1..1000`; verify all results and compute baseline aggregate score.

### Stage C: Small optimization benchmark
Use a fixed subset (for example `n=2..30`) and fixed seeds. Compare:
- baseline grid
- alternative initial layouts
- annealing only
- annealing plus local refinement

### Stage D: Scaling
Increase to `n=31..200`, measure runtime and collision-check counts, and add spatial acceleration where required.

### Stage E: Full run
Run all puzzle sizes with configurable per-puzzle budgets. Save best feasible solutions and logs.

### Stage F: Final audit
Re-load artifacts and validate from scratch, then generate and re-read the CSV before upload.

## 9. Benchmark fairness
- Use the same puzzle subset and seed list when comparing strategies.
- Record config and code revision.
- Compare aggregate score, per-puzzle score distribution, valid-solution rate, and runtime.
- Report median and best score across restarts where useful.
- Do not compare a short run against a much longer run without stating the budget difference.

## 10. Acceptance thresholds
- Geometry and submission tests pass.
- No invalid incumbent is persisted.
- Optimized solution never silently replaces a better valid solution.
- Full submission has 500,500 rows.
- Score improvement is measured against the baseline using the same scoring code.
