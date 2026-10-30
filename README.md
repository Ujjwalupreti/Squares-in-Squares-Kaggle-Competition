# Squares in Squares — Competitive Geometric Optimization System
## Kaggle Competition: Squares in Squares

[![Kaggle Notebook](https://img.shields.io/badge/Kaggle-Notebook-20BEFF.svg)](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization)
[![Leaderboard Score](https://img.shields.io/badge/Kaggle%20Score-22.2991515-gold.svg)](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization)
[![Leaderboard Rank](https://img.shields.io/badge/Leaderboard%20Rank-600-blueviolet.svg)](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization)
[![Personal Best](https://img.shields.io/badge/Personal%20Best-22.2991515-success.svg)]()
[![SAT Validation](https://img.shields.io/badge/SAT%20Overlaps-0.0%20(Certified)-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-126%20passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

A complete, production-grade Python computational geometry package and optimization pipeline designed for the Kaggle **Squares in Squares** competition. It features an exact Separating Axis Theorem (SAT) collision engine, multi-start simulated annealing, Contact-LP Squeeze (HiGHS), Neighbour Transfer heuristics, certified multi-angle cluster packings beating published records, and an audited 500,500-row submission builder.

- **Kaggle Notebook**: [Squares in Squares: Geometric Optimization](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization)
- **Current Official Score**: **`22.2991515337`** (Rank 600, 10 submissions, zero overlap penalty)
- **Score Improvement**: `22.2999557130` $\to$ **`22.2991515337`** ($\Delta S = -0.00080418$)
- **Next Target Milestone**: **`22.2560322816`** ($\Delta S = 0.0431192521$ remaining)
- **Long-Term Continuum Limit**: **`22.1400000000`**

---

## 1. Project Objective & Scoring

The goal is to pack $n$ identical $1 \times 1$ unit squares ($n = 1, \dots, 1000$) inside the smallest possible axis-aligned square container of side length $L_n$ without interior overlap.

Each square $i \in \{0, \dots, n-1\}$ is defined by center coordinates $(x_i, y_i)$ and rotation angle $\theta_i \in [0, \pi/2)$.

The official competition scoring function evaluates relative excess above the theoretical area lower bound $\sqrt{n}$:

$$\text{score}(n) = \frac{L_n}{\sqrt{n}} - 1$$

$$\text{Aggregate Score} = \sum_{n=1}^{1000} \text{score}(n)$$

- **Lower is better.**
- Perfect squares $n = k^2$ pack into $L = k$, achieving an optimal $\text{score}(k^2) = 0.0$.
- **Current Verified Leaderboard Score**: **`22.2991515337`** (Rank 600, certified 0 overlaps across all 1,000 puzzles).

### Optimization Progress Tracking

| Milestone / Pipeline Stage | Score | $\Delta S$ vs. Baseline | Status |
|:---|:---:|:---:|:---:|
| **Deterministic Grid Baseline** ($L = \lceil\sqrt{n}\rceil$) | `28.937670` | Reference | Verified & Audited |
| **Initial Incumbent Store** | `22.299956` | $-6.637714$ | Accepted by Kaggle |
| **Certified Multi-Angle Upgrades** ($n=232, 260, 299$) | **`22.299152`** | **$-6.638518$** | **Current Leaderboard (Rank 600)** |
| **Target Phase 1: Transition Grid Compression** ($n \in [184, 255]$) | `22.256032` | $-6.681638$ | Active Target ($\Delta S = 0.043119$) |
| **Target Phase 2: Theoretical Dense Continuum Bound** | `22.140000` | $-6.797670$ | Long-term Target |

---

## 2. Key Optimization Milestones & Breakthroughs

### 2.1 Certified Upgrades Beating Classical Records ($n = 232, 260, 299$)
Historical catalogue records (Friedman/Ellsworth) enforce rigid single-angle diagonal bands (e.g., all tilted squares locked at $24.3^\circ$). We developed **asymmetric multi-angle cluster relaxation**, allowing tilted squares to split into corner clusters with multi-angle relaxation (14–21 distinct angles), pulling the boundary squares tighter to the walls and contracting the bounding square:

| Puzzle $n$ | Classical Catalogue Record | Our Certified Packing | Improvement ($\Delta L$) | Score Reduction ($\Delta \text{score}$) |
|:---:|:---:|:---:|:---:|:---:|
| **$n = 299$** | $L = 17.822876$ | **$L = 17.813286$** | $-0.009590$ | **$-0.00055461$** |
| **$n = 260$** | $L = 16.645753$ | **$L = 16.642149$** | $-0.003604$ | **$-0.00022354$** |
| **$n = 232$** | $L = 15.764174$ | **$L = 15.763778$** | $-0.000396$ | **$-0.00002603$** |
| **Total** | — | — | — | **$-0.00080418$** |

### 2.2 Analytical $N=5$ Positive Clearance Safeguard
To guarantee zero-overlap validation under Kaggle's strict interval arithmetic (`mpmath`), we enforce an analytical positive clearance buffer ($\epsilon = 10^{-7}$):
$$L_5 = 2.0 + \frac{1}{\sqrt{2}} + 10^{-7} \approx 2.7071068812$$
This completely prevents floating-point rounding errors and protects against disqualification penalties.

---

## 3. Repository Structure

```text
├── config/                     YAML optimization configurations (default, fast, benchmark)
├── docs/                       Architecture, design, PRD, rules, tasks, and strategy reports
│   ├── ARCHITECTURE.md         System architecture and module dataflow
│   ├── DESIGN.md               Technical design and numerical tolerances
│   ├── PRD.md                  Product requirements and acceptance criteria
│   ├── RULES.md                Official competition rules and verification contract
│   ├── TASKS.md                Task tracking plan with verified evidence
│   └── score_improvement_report.md Detailed audit of optimization benchmarks
├── notebooks/                  Kaggle publication-ready notebooks
│   ├── squares_in_squares.ipynb Complete self-contained competition notebook (scores 22.2991515)
│   └── kernel-metadata.json    Kaggle CLI kernel configuration
├── scripts/                    Executable CLI commands
│   ├── ingest_solutions.py     Automated gatekeeper for merging external candidates (tol=0.0)
│   ├── solve_neighbor_transfer.py Automated Neighbor-Transfer & HiGHS LP squeeze solver
│   ├── run_baseline.py         Generate grid baseline for n=1..1000
│   ├── run_optimization.py     Run multi-start solver across puzzle ranges
│   ├── run_benchmark.py        Controlled benchmark with fixed seeds
│   ├── run_validation.py       Independent geometry validation of stored solutions
│   ├── build_submission.py     Compile solution records into compliant CSV with score tracking
│   └── audit_submission.py     Independent audit of submission CSV
├── src/squares_in_squares/     Production Python package
│   ├── geometry/               Square representation, transforms, bounds, SAT, spatial index
│   ├── packing/                Layout strategies (grid, staggered, certified upgrades)
│   ├── optimization/           Moves, annealing, local search, restart, solver
│   ├── storage/                Atomic checkpoints and versioned SolutionStore
│   ├── validation/             Independent packing and submission validators
│   ├── submission/             CSV generation and audit routines
│   ├── experiments/            Benchmarking suite
│   ├── config.py               Configuration loading and validation
│   └── cli.py                  Unified CLI (`squares-in-squares`)
├── submissions/                Submission artifacts and audit reports
│   ├── submission_improved.csv Latest certified submission (score 22.2991515, 500,500 rows)
│   ├── submission.csv          Active submission file (score 22.2991515)
│   ├── submission_best_22_299956.csv Immutable baseline reference file
│   └── experiments/manifest.json Experiment manifest and benchmark tracking
└── tests/                      Pytest test suite (103 unit and integration tests)
    └── unit/                   Unit tests for geometry, moves, packing, certified upgrades, and validation
```

---

## 4. Operational Guide & CLI Usage

The package provides a unified CLI `squares-in-squares` and standalone scripts in `scripts/`:

### 4.1 Running the Baseline
Generate deterministic grid packings for all 1,000 puzzles:
```bash
python scripts/run_baseline.py
# Or via CLI:
squares-in-squares baseline --n-min 1 --n-max 1000
```
- **Output Score**: `28.937670`
- **Integrity**: 1,000 valid solutions stored in `artifacts/solutions/`.

### 4.2 Ingesting Candidate Solutions with Strict SAT Gatekeeper
To import and merge candidate solutions safely:
```bash
python scripts/ingest_solutions.py --file path/to/candidate.csv --tolerance 0.0
```
- Strictly validates every candidate puzzle against the Separating Axis Theorem (SAT) with **zero tolerance** (`0.0`).
- Overwrites stored incumbents **only** if the incoming solution is 100% valid and strictly improves the puzzle's side length $L$.

### 4.3 Running Neighbor-Transfer & Squeeze Optimization
```bash
python scripts/solve_neighbor_transfer.py --targets 184 212 242
```

### 4.4 Generating & Auditing the Submission CSV
Build and audit the 500,500-row competition submission file:
```bash
python scripts/build_submission.py
python scripts/audit_submission.py submissions/submission_improved.csv
```
Audit output verification:
```text
Auditing submission file: submissions/submission_improved.csv (n=1..1000)...
AUDIT PASSED!
  Total rows:      500500 (expected: 500500)
  Unique puzzles:  1000
  Aggregate score: 22.2991515338
  Collisions:      0
```

---

## 5. Kaggle Notebook Deployment

The complete, self-contained Jupyter notebook is published at [Squares in Squares: Geometric Optimization](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization).

### Features:
1. **Automated Dataset Discovery**: Inspects attached Kaggle datasets in `/kaggle/input/` while safely ignoring unoptimized sample submission grids.
2. **Embedded Certified Upgrades**: Contains hardcoded coordinates for record-breaking packings ($n = 232, 260, 299$).
3. **$N=5$ Safeguard**: Automatically enforces the analytical $10^{-7}$ positive clearance buffer.
4. **Instant Score**: Directly writes `/kaggle/working/submission.csv` scoring **`22.2991515337`** (Personal Best, Rank 600).

---

## 6. Test Suite & Verification

Run the full pytest test suite:
```bash
python -m pytest tests/ -v
```
- **126 tests pass (103 unit, 23 integration)**:
  - `test_geometry.py`: Half-extents, corner formulas, axis-aligned bounds, SAT collision detection, spatial index.
  - `test_certified_upgrades.py`: Verifies zero overlaps (tolerance 0.0) for all record-breaking layouts.
  - `test_moves.py`: Single translation, rotation, combined moves, group translation, boundary detection.
  - `test_objective.py`: Smooth penalty, container objective, monotonicity.
  - `test_packing.py`: Grid packing, staggered packing, rotated pattern validity.
  - `test_optimization.py`: Simulated annealing, local search, multi-start restart orchestration.
  - `test_integration.py`: Atomic checkpoint writing, corrupted checkpoint recovery, resume semantics.
  - `test_cli.py`: Command-line interface end-to-end execution.

---

## 7. Roadmap to 22.256032 & 22.14

1. **Grid Transition Ensembling**:
   - 422 puzzles currently use integer grid packings with empty perimeter slots ($n \in [184, 195]$, $n \in [212, 224]$, $n \in [242, 255]$).
   - Ingesting validated non-grid cluster configurations across these transition bands reduces container sizes by $\approx 0.1 - 0.3$, bridging the $\Delta S \approx 0.043$ gap to reach **`22.256032`**.
2. **CUDA / High-Performance Coordinate Annealing**:
   - Running GPU-accelerated soft-body repulsion across large $n$ ($500 \le n \le 1000$) to push dense packing density toward the theoretical $\sqrt{n}$ lower bound (**`22.140000`**).
