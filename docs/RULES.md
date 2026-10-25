# Project Rules for AI-Assisted Development

These rules apply to contributors and AI coding agents working on Squares in Squares.

## 1. Before changing code
1. Read `PRD.md`, `ARCHITECTURE.md`, `DESIGN.md`, `TASKS.md`, and this file.
2. Inspect the existing implementation and tests.
3. State the intended changes and affected files for non-trivial tasks.
4. Do not invent competition requirements; use the competition's official specification and sample submission.

## 2. Architecture rules
- Keep geometry, packing strategies, optimization, validation, persistence, and submission code separate.
- Do not put all functionality in one notebook or one oversized module.
- Keep the independent validator separate from optimizer penalty calculations.
- Do not let UI/notebook display code become a dependency of the solver.
- Use type hints for public functions where practical.
- Keep functions focused and add docstrings for non-obvious geometry.

## 3. Geometry and numerical rules
- Use radians for angles.
- Use side length `1` consistently.
- Document all tolerances and why they are used.
- Test edge/corner contact, near-contact, rotations, and large/small coordinate values.
- Never treat a low overlap penalty as proof of validity.
- Independently recompute bounds and collisions before saving an incumbent or final output.
- Reject NaN and infinite values.

## 4. Optimization rules
- Preserve the best feasible incumbent independently from current search state.
- Never overwrite a better validated solution with a worse or invalid candidate.
- Record seed, parameters, iteration count, and runtime.
- Make iteration limits and time budgets configurable.
- Every new move family or heuristic must have a benchmark demonstrating its effect.
- Do not claim global optimality unless it is mathematically proven.

## 5. Testing rules
- Add unit tests for every new geometry edge case.
- Add regression tests for every bug fixed.
- Run unit tests before integration tests.
- Run a small end-to-end submission test before any full 1,000-puzzle run.
- Do not mark a task complete if tests were not run; report tests that could not be run.

## 6. Submission rules
- Preserve exact column order: `id,n,square_id,x,y,angle`.
- Use decimal numeric values, not formatted strings with commas or units.
- IDs must be unique and sequential.
- Each puzzle `n` must contain exactly `n` squares with IDs `0..n-1`.
- Validate all packings after reloading the generated CSV.
- Stop submission generation if an audit fails.

## 7. Persistence and reproducibility
- Save a checkpoint after configured intervals and on meaningful improvements.
- Use atomic writes where possible.
- Keep raw experiment logs; do not manually alter logged scores.
- Store config and code revision alongside results.
- Never rely on Kaggle's ephemeral working directory as the only copy of important artifacts.

## 8. Security and repository hygiene
- Never commit credentials, personal access tokens, or private keys.
- Do not hardcode secrets in notebooks.
- Keep generated large artifacts out of Git unless intentionally versioned.
- Use `.gitignore` for caches, temporary files, and local environments.

## 9. AI agent task protocol
For each task:
1. Read the relevant docs.
2. Inspect current code.
3. Make the smallest coherent change.
4. Add or update tests.
5. Run relevant tests and static checks.
6. Review changed files for unrelated modifications.
7. Update `TASKS.md` and documentation if behavior or architecture changes.
8. Report files changed, tests run, results, and remaining risks.

## 10. Required implementation report
Every substantial code task must end with:
- Summary of changes.
- Files changed.
- Commands/tests run and their results.
- Validation evidence.
- Known limitations or follow-up tasks.
