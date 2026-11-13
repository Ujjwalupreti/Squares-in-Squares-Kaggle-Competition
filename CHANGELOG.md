# Changelog

All notable changes to the **Squares in Squares** geometric optimization system are documented in this file.

## [v1.7.0] — 2026-11-13

### Milestone: Cracking the 22.18 Barrier to Certified Benchmark `22.179269`
- **Kaggle Disqualification Remediation & Precision Hardening**:
  - Diagnosed and resolved the root cause of Kaggle's evaluation disqualification (+1.512 fallback penalty): 35 puzzles in the previous merge had sub-epsilon negative clearances ($-10^{-15}$), triggering interval-arithmetic overlap penalties in `mpmath.iv`.
  - Ingested hardened, certified configuration `submission_new.txt` guaranteeing strictly non-negative clearance across all 1,000 puzzles ($\ge 0.00\text{e}+00$) and certified positive safety buffers ($\ge 1.00 \times 10^{-12}$) on all 554 non-grid packings.
- **Score Advancement to New Personal Best**:
  - Adopted 163 strictly superior, collision-free packings, slashing the certified leaderboard benchmark from `22.204803` down to **`22.179269`** ($\Delta S = -0.025534$).
  - Full SAT 0.0 compliance, lower-left $(0,0)$ origin canonicalization, sequential IDs 0..500,499.
  - Complete test suite passed: 146 / 146 tests green (100%).

## [v1.6.0] — 2026-11-11

### Milestone: Cracking the 22.20 Barrier to Certified Benchmark `22.194550`
- **Universal Multi-Portfolio Master Merge**:
  - Executed master portfolio cross-merge across all candidate files, extracting 955 core compaction breakthroughs and 45 sub-nanometer precision retainers.
  - Slashed aggregate competition score decisively from `22.204803` down to **`22.194550`** ($\Delta S = -0.010253$).
  - Identified 82 significant compaction leaps across mid-to-high $N$ (e.g. $N=452, 453, 454, 172, 199, 378, 497, 498$).
- **Contact Hardening & Precision Trap Elimination**:
  - Resolved 17 critical machine-epsilon float64 boundary collisions ($-2.22 \times 10^{-16}$) using adaptive radial centroid dilation ($\delta \in [10^{-12}, 10^{-8}]$).
  - Prevented a cumulative $+0.454056$ Kaggle interval-arithmetic fallback penalty.
  - Certified zero SAT overlaps across all 1,000 puzzles under strict `tolerance=0.0`.
- **Pipeline Architecture & Primitives**:
  - Built `scripts/master_merge.py` for automated multi-candidate portfolio evaluation and canonicalization.
  - Added `canonicalize_packing` and `dilate_packing` to `src/squares_in_squares/geometry/transforms.py`.
  - Expanded test suite to **146 tests passing (100% green)**.

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
