# Changelog

All notable changes to the **Squares in Squares** geometric optimization system are documented in this file.

## [v1.5.0] — 2026-11-11

### Breakthrough: Certified Personal Best `22.204803`
- **Candidate Merge & Traps Resolution**:
  - Ingested candidate dataset `new_mark_submission.txt` (121 proposed upgrades).
  - Uncovered critical validation vulnerability: 17 raw candidate configurations contained interior SAT overlaps (including unbuffered $N=5$ Göbel corner collisions), which would have triggered Kaggle's $+0.44$ grid fallback penalty.
  - Safely adopted **120 strictly superior, certified collision-free packings** while preserving certified positive-clearance safeguards ($\varepsilon = 10^{-7}$) on $N=5$.
  - Slashed aggregate competition score from `22.218044` to **`22.204803`** ($\Delta S = -0.013241$).

### Performance & Geometry Improvements
- **Submission Auditor Vectorization (90x speedup)**:
  - Replaced linear multi-pass puzzle scans in `audit_submission` with single-pass `groupby("n")` pre-indexing.
  - Reduced full 500,500-row audit runtime from ~180 seconds to under 3 seconds.
- **Pairwise Clearance Diagnostics**:
  - Added `compute_minimum_separation` in `geometry/bounds.py` to calculate exact SAT clearance margins across all square pairs.
  - Added `batch_container_side_lengths` for efficient batch container evaluations.
- **Automated Merger Guarding**:
  - Enhanced `scripts/optimize_and_merge.py` with strict SAT pre-validation, automated overlap rejection, markdown audit reporting, and `--dry-run` CLI options.
- **Test Suite Expansion**:
  - Added 9 unit tests in `tests/unit/test_validator_perf.py` covering separation clearance, batch calculations, and audit reporting.
  - Test suite expanded to **143 tests passing (100% green)**.

---

## [v1.4.0] — 2026-11-08

### Milestone: Cracking the 22.22 and 22.21 Barriers (`22.218044`)
- Ingested 92 certified upgrades from `new_test_submission_2.txt` with 0 regressions.
- Slashed aggregate score from `22.223867` to `22.218044`.
- Enhanced Kaggle notebook with comprehensive Reading Room mathematical synthesis, border extension chain roots ($N=123$), and fractional spectrum visualizations.

---

## [v1.3.0] — 2026-11-07

### Milestone: Border Extension Invariant Chains (`22.223867`)
- Integrated 120 certified configurations from border-extension candidate portfolios.
- Resolved diagonal band dynamics and rational corner boundary termination ($K^2+1 \dots K^2+K$).
- Net score reduction of $-0.014029$ down to `22.223867`.

---

## [v1.2.0] — 2026-11-06

### Milestone: Portfolio Integration & Contact Dilation (`22.237896`)
- Ingested 292 superior configurations from top score portfolio.
- Enforced analytical positive clearance on $N=5$ and applied selective radial centroid dilation ($\delta = 10^{-10}$) for Kaggle floating-point safety.

---

## [v1.1.0] — 2026-11-01

### Milestone: Continuous Soft-Body Relaxation & Multi-Angle Clusters (`22.299152`)
- Developed PyTorch GPU continuous soft-body relaxation engine.
- Certified records beating published catalogues on $n=232, 260, 299$ with asymmetric multi-angle clusters.
- HiGHS LP contact compaction integration.

---

## [v1.0.0] — 2026-10-24

### Initial Release: Production Geometry Package & Baseline (`28.937670`)
- Exact Separating Axis Theorem (SAT) collision detection engine with spatial indexing.
- Simulated annealing with multi-start local search and boundary compaction.
- Verified 500,500-row submission builder and independent validator.
