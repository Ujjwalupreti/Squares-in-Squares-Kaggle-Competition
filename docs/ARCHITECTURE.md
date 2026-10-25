# System Architecture
## Squares in Squares Packing Optimizer

## 1. Architectural goals
- Keep geometry calculations deterministic and testable.
- Keep search heuristics independent from correctness validation.
- Preserve the best feasible result for each puzzle.
- Scale from small test cases to all 1,000 puzzle sizes.
- Make experiments resumable and comparable.

## 2. High-level pipeline
1. Load configuration and puzzle range.
2. Generate an initial candidate layout.
3. Evaluate bounds and search objective.
4. Propose local or collective moves.
5. Evaluate candidate and apply acceptance policy.
6. Independently validate feasible candidates.
7. Save incumbent/checkpoint.
8. Repeat until budget is exhausted.
9. Reload all incumbents and independently validate them.
10. Build, reload, and audit the submission CSV.

## 3. Component responsibilities
### Puzzle/configuration
Defines valid puzzle sizes, seeds, run budgets, and algorithm parameters.

### Geometry engine
- `square.py`: square data representation and basic invariants.
- `transforms.py`: local axes and corner coordinates.
- `bounds.py`: exact axis-aligned extents and container side.
- `sat.py`: pairwise square interior-overlap test.
- `spatial_index.py`: broad-phase filtering for likely collisions.

### Packing strategies
- `grid.py`: guaranteed-feasible axis-aligned baseline.
- `staggered.py`: alternative initial patterns.
- `rotated_patterns.py`: structured rotated candidates.
- `warm_start.py`: load and transform previous valid layouts when useful.

### Optimization engine
- `objective.py`: container size and optional overlap penalty.
- `moves.py`: translation, rotation, boundary, and group moves.
- `annealing.py`: temperature schedule and acceptance probability.
- `local_search.py`: focused improvement after global exploration.
- `restart.py`: multi-start orchestration.
- `solver.py`: top-level solver and incumbent management.

### Validation
The final validator is independent of the optimization shortcut/penalty code. It checks finite values, pairwise geometry, count, and score.

### Storage
- `checkpoint.py`: serializes resumable state and metadata.
- `solution_store.py`: stores best validated solution per `n`.
- Logs contain experiment metadata and progress.

### Submission
- `build_submission.py`: writes the competition schema.
- `audit_submission.py`: reloads the CSV and checks structure and geometry.

## 4. Data contracts
### Square
`(x: float, y: float, angle: float)` where `(x,y)` is the center and `angle` is in radians.

### Packing
An ordered collection of exactly `n` square triples.

### Validated solution record
- `n`
- `squares`
- `container_length`
- `score`
- `seed`
- `strategy`
- `runtime_seconds`
- `validator_version`
- `created_at` or run identifier

### Submission row
`id,n,square_id,x,y,angle`

## 5. Geometry formulas
For square `i` with angle `theta_i`, its half-extent on x and y is:
`h_i = (abs(cos(theta_i)) + abs(sin(theta_i))) / 2`

Container bounds:
- `xmin = min(x_i - h_i)`
- `xmax = max(x_i + h_i)`
- `ymin = min(y_i - h_i)`
- `ymax = max(y_i + h_i)`
- `L = max(xmax - xmin, ymax - ymin)`

SAT tests the two local axes from each square. A separating axis means the square interiors do not overlap. Edge and corner contact are allowed. Numerical tolerance must be documented and covered by tests.

## 6. Optimization policy
The current search state may be infeasible if the chosen search method uses overlap penalties. The incumbent must always be feasible according to the independent validator. An invalid candidate must never replace a valid incumbent.

Recommended progression:
1. Grid baseline.
2. Multiple candidate layouts.
3. Simulated annealing with translations and rotations.
4. Collective moves and adaptive step sizes.
5. Local refinement and time allocation based on observed improvement.

The search objective can use an overlap penalty, but that penalty is not proof of feasibility.

## 7. Performance strategy
- Start with straightforward pairwise SAT checks for small `n`.
- Add broad-phase AABB or spatial-grid filtering as `n` grows.
- Avoid recomputing unaffected pair relationships when implementing incremental moves.
- Use a deterministic seed per `(n, run_id)`.
- Track wall-clock budgets and best-so-far results.

## 8. Persistence and recovery
Checkpoint should include:
- schema/version
- puzzle size and seed
- current search state
- best feasible incumbent and score
- iteration and temperature
- optimizer/config version
- random generator state when exact continuation is required

Write checkpoints atomically where possible. If loading fails, preserve the last known valid solution and restart safely.

## 9. Error handling
- Invalid `n`: fail fast.
- Non-finite coordinates: reject candidate.
- Invalid checkpoint: quarantine/report and continue from incumbent.
- Validation failure: never save as incumbent.
- Submission audit failure: stop export/finalization and report offending puzzle/row.

## 10. Deployment model
The primary runtime is a Kaggle Notebook or script environment. Source code is versioned in GitHub. Checkpoints and solution artifacts must be saved outside ephemeral notebook storage when long-running experiments need to survive session resets.
