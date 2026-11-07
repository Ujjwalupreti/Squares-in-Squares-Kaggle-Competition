# Squares in Squares — Competitive Geometric Optimization System

## Kaggle Competition: Squares in Squares

[![Kaggle Notebook](https://img.shields.io/badge/Kaggle-Notebook-20BEFF.svg)](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization)
[![Certified Score](<https://img.shields.io/badge/Certified%20Score-22.223867-gold.svg>)](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization)
[![Leaderboard Rank](<https://img.shields.io/badge/Leaderboard%20Rank-Top--Tier-blueviolet.svg>)](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization)
[![Personal Best](<https://img.shields.io/badge/Personal%20Best-22.223867-success.svg>)]()
[![SAT Validation](<https://img.shields.io/badge/SAT%20Overlaps-0.0%20(Certified)-brightgreen.svg>)]()
[![Tests](<https://img.shields.io/badge/tests-134%20passed-brightgreen.svg>)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

A complete, production-grade Python computational geometry package and optimization pipeline designed for the Kaggle **Squares in Squares** competition. It features an exact Separating Axis Theorem (SAT) collision engine, multi-start simulated annealing, HiGHS Linear Programming (LP) Contact Compaction, PyTorch GPU Continuous Soft-Body Relaxation, certified multi-angle cluster packings beating published records, automated greedy merging with selective contact dilation ($\delta = 10^{-10}$), interactive visual analytics, and an audited 500,500-row submission builder.

- **Kaggle Notebook**: [Squares in Squares: Geometric Optimization](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization)
- **Certified Personal Best**: **`22.22386681`** (Audited with zero overlap penalty across 1,000 puzzles)
- **Net Improvement**: `22.23789565` $\to$ **`22.22386681`** ($\Delta S = -0.01402885$)
- **Upgraded Layouts**: **120 puzzles** strictly improved over previous incumbent store
- **Next Target Milestone**: **`22.21000000`** ($\Delta S = 0.01386681$ remaining)
- **Long-Term Continuum Limit**: **`22.14000000`**

---

## 1. Project Objective & Scoring

The goal is to pack $n$ identical $1 \times 1$ unit squares ($n = 1, \dots, 1000$) inside the smallest possible axis-aligned square container of side length $L_n$ without interior overlap.

Each square $i \in \{0, \dots, n-1\}$ is defined by center coordinates $(x_i, y_i)$ and rotation angle $\theta_i \in [0, \pi/2)$.

The official competition scoring function evaluates relative excess above the theoretical area lower bound $\sqrt{n}$:

$$
\text{score}(n) = \frac{L_n}{\sqrt{n}} - 1
$$

$$
\text{Aggregate Score} = \sum_{n=1}^{1000} \text{score}(n)
$$

- **Lower is better.**
- Perfect squares $n = k^2$ pack into $L = k$, achieving an optimal $\text{score}(k^2) = 0.0$.
- **Current Verified Certified Score**: **`22.22386681`** (Certified 0 overlaps across all 1,000 puzzles).

### Optimization Progress Tracking

| Milestone / Pipeline Stage                                                   |          Score          | $\Delta S$ vs. Baseline |                  Status                  |
| :--------------------------------------------------------------------------- | :---------------------: | :-----------------------: | :--------------------------------------: |
| **Deterministic Grid Baseline** ($L = \lceil\sqrt{n}\rceil$)                 |      `28.937670`        |         Reference         |            Verified & Audited            |
| **Initial Incumbent Store**                                                  |      `22.299956`        |       $-6.637714$         |            Accepted by Kaggle            |
| **Certified Multi-Angle Upgrades** ($n=232, 260, 299$)                       |      `22.299152`        |       $-6.638518$         |            Leaderboard Rank 600          |
| **Greedy Merge & Selective Dilation (248 Upgraded Puzzles)**                 |      `22.257047`        |       $-6.680623$         |              Verified Best               |
| **Portfolio Breakthrough (292 Upgraded Puzzles)**                            |      `22.237896`        |       $-6.699774$         |              Audited Baseline            |
| **Border Extension & Multi-Angle Compaction (120 Upgraded Puzzles)**         | **`22.223867`**         |     **$-6.713803$**       | **Current Certified Best (0.0 SAT)**     |
| **Target Phase 1: Contact-LP Compaction on 418 Grid Puzzles**                |      `22.210000`        |       $-6.727670$         | Active Target ($\Delta S = 0.013867$)    |
| **Target Phase 2: Theoretical Dense Continuum Bound**                        |      `22.140000`        |       $-6.797670$         |             Long-term Target             |

---

## 2. Key Optimization Milestones & Breakthroughs

### 2.1 Certified Upgrades Beating Classical Records ($n = 232, 260, 299$)

Historical catalogue records enforce rigid single-angle diagonal bands (e.g., all tilted squares locked at $24.3^\circ$). We developed **asymmetric multi-angle cluster relaxation**, allowing tilted squares to split into corner clusters with multi-angle relaxation (14–21 distinct angles), pulling the boundary squares tighter to the walls and contracting the bounding square:

|     Puzzle $n$     | Classical Catalogue Record |    Our Certified Packing    | Improvement ($\Delta L$) | Score Reduction ($\Delta \text{score}$) |
| :-------------------: | :------------------------: | :-------------------------: | :------------------------: | :---------------------------------------: |
| **$n = 299$** |     $L = 17.822876$     | **$L = 17.801004$** |       $-0.021872$       |         **$-0.00126487$**         |
| **$n = 260$** |     $L = 16.645753$     | **$L = 16.633983$** |       $-0.011770$       |         **$-0.00072993$**         |
| **$n = 232$** |     $L = 15.764174$     | **$L = 15.761410$** |       $-0.002764$       |         **$-0.00018146$**         |
|    **Total**    |             —             |             —             |             —             |         **$-0.00217626$**         |

### 2.2 Analytical $N=5$ Positive Clearance Safeguard

To guarantee zero-overlap validation under Kaggle's strict interval arithmetic (`mpmath`), we enforce an analytical positive clearance buffer ($\epsilon = 10^{-7}$):

$$
L_5 = 2.0 + \frac{1}{\sqrt{2}} + 10^{-7} \approx 2.7071068812
$$

This completely prevents floating-point rounding errors and protects against disqualification penalties.

### 2.3 Separating Axis Theorem (SAT) Zero-Tolerance Collision Certification (0.0 Overlaps)

The badge `SAT Overlaps: 0.0 (Certified)` guarantees that every configuration in the submission is mathematically and numerically collision-free:

1. **Mathematical Formulation (Separating Axis Theorem)**:
   In 2D Euclidean geometry, two convex polygons (here, $1 \times 1$ oriented unit squares) do not overlap if and only if there exists a separating axis $\mathbf{a}$ upon which their 1D orthogonal projections are disjoint. For any pair of squares $A$ and $B$, the set of candidate separating axes consists solely of the 4 unique edge normal vectors (2 from $A$ and 2 from $B$):
   $$\mathbf{a} \in \{\mathbf{e}_{1}^A, \mathbf{e}_{2}^A, \mathbf{e}_{1}^B, \mathbf{e}_{2}^B\}$$
   The projection half-width (radius) of an oriented unit square onto axis $\mathbf{a}$ is given by:
   $$r(\mathbf{a}) = \frac{1}{2} |\mathbf{a} \cdot \mathbf{e}_1| + \frac{1}{2} |\mathbf{a} \cdot \mathbf{e}_2|$$
   If the center-to-center distance $\mathbf{d} = \mathbf{c}_B - \mathbf{c}_A$ projected onto any axis $\mathbf{a}$ satisfies:
   $$|\mathbf{d} \cdot \mathbf{a}| \ge r_A(\mathbf{a}) + r_B(\mathbf{a}) - \tau$$
   then axis $\mathbf{a}$ is a separating axis, proving the squares' interiors are disjoint.
2. **Why Strict 0.0 Tolerance Matters**:
   Kaggle's official submission evaluation engine runs on multi-precision interval arithmetic (`mpmath`). If any square pair intersects by even $\approx 10^{-15}$ (due to floating-point truncation), the entire puzzle is disqualified or assigned an invalid penalty.
3. **Exhaustive Certification**:
   Our validation suite audits all 500,500 squares across all 1,000 puzzles ($> 166.8$ million candidate checks) with zero overlap tolerance (`\tau = 0.0`), guaranteeing 100% compliance with Kaggle's evaluation rules.

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
│   ├── squares_in_squares.ipynb Complete self-contained notebook (scores 22.23789565 with visual analytics)
│   └── kernel-metadata.json    Kaggle CLI kernel configuration
├── scripts/                    Executable CLI commands
│   ├── heavy_optimizer.py      Multi-core CPU optimizer with target puzzle filtering
│   ├── optimize_and_merge.py   Automated greedy packing merger and contact dilation optimizer
│   ├── optimize_transitions.py Transition boundary optimizer with SAT certification
│   ├── ingest_solutions.py     Automated gatekeeper for merging external candidates (tol=0.0)
│   ├── solve_neighbor_transfer.py Neighbor-Transfer & HiGHS LP squeeze solver
│   ├── run_baseline.py         Generate grid baseline for n=1..1000
│   ├── run_optimization.py     Run multi-start solver across puzzle ranges
│   ├── run_benchmark.py        Controlled benchmark with fixed seeds
│   ├── run_validation.py       Independent geometry validation of stored solutions
│   ├── build_submission.py     Compile solution records into compliant CSV with score tracking
│   └── audit_submission.py     Independent audit of submission CSV
├── src/squares_in_squares/     Production Python package
│   ├── geometry/               Square representation, transforms, bounds, SAT, spatial index
│   ├── packing/                Layout strategies (grid, staggered, certified upgrades, diagonal stripes)
│   ├── optimization/           Moves, annealing, contact LP (HiGHS), pocket insertion, local search, solver
│   ├── storage/                Atomic checkpoints and versioned SolutionStore
│   ├── validation/             Independent packing and submission validators
│   ├── submission/             CSV generation and audit routines
│   ├── experiments/            Benchmarking suite
│   ├── config.py               Configuration loading and validation
│   └── cli.py                  Unified CLI (`squares-in-squares`)
├── submissions/                Submission artifacts and audit reports
│   ├── submission_improved.csv Latest certified submission (score 22.22386681, 500,500 rows)
│   ├── submission.csv          Active submission file (score 22.22386681)
│   └── experiments/manifest.json Experiment manifest and benchmark tracking
└── tests/                      Pytest test suite (134 unit and integration tests)
    ├── unit/                   Unit tests for geometry, moves, packing, certified upgrades, contact LP, and validation
    └── integration/            Integration tests for baseline, solution store, checkpoints, and submissions
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

### 4.3 Running Greedy Contact Merger & Safe Dilation

```bash
python scripts/optimize_and_merge.py --base submissions/submission_improved.csv --candidate top_score_file.txt --dilation 1e-10 --output submissions/submission_improved.csv
```

### 4.4 Generating & Auditing the Submission CSV

Build and audit the 500,500-row competition submission file:

```bash
python scripts/build_submission.py
python scripts/audit_submission.py submissions/submission_improved.csv
```

Audit output verification:

```text
Auditing submission file: submissions/submission.csv (n=1..1000)...
AUDIT PASSED!
  Total rows:      500500 (expected: 500500)
  Unique puzzles:  1000
  Aggregate score: 22.237896
  Collisions:      0
```

---

## 5. Kaggle Notebook Deployment & Visual Analytics

The complete, self-contained Jupyter notebook is published at [Squares in Squares: Geometric Optimization](https://www.kaggle.com/code/ujjwalupreti/squares-in-squares-geometric-optimization).

### Features:

1. **Automated Dataset Discovery**: Inspects attached Kaggle datasets in `/kaggle/input/` while safely ignoring unoptimized sample submission grids.
2. **HiGHS LP Contact Compaction**: Uses active-contact linear programming to squeeze translation coordinates into contact manifolds in milliseconds.
3. **PyTorch GPU Soft-Body Continuous Relaxation**: Differentiable repulsive potential field optimizing $(x, y, \theta)$ simultaneously on GPU to resolve dense topological jams.
4. **Visual Analytics & Exploratory Data Analysis (EDA)**:
   - **Global Metric Profile**: Dual-panel plot of excess slack $\left(\frac{L_n}{\sqrt{n}} - 1\right)$ across all 1,000 puzzles and slack distribution histogram.
   - **2D Geometry Packing Visualizer**: 4-panel visual diagram for $n = 4, 5, 10, 11$, displaying tilted squares, rotation angles, and container boundaries.
   - **Interactive Function**: `plot_packing(squares, n)` to visualize any puzzle configuration on demand.
5. **$N=5$ Safeguard & Contact Dilation**: Automatically enforces the analytical $10^{-7}$ positive clearance buffer and sub-micron radial dilation ($\delta = 10^{-10}$).
6. **Instant Score**: Directly writes `/kaggle/working/submission.csv` scoring **`22.237896`** with zero overlap penalties.

---

## 6. Test Suite & Verification

Run the full pytest test suite:

```bash
python -m pytest tests/ -v
```

- **134 tests pass (111 unit, 23 integration)**:
  - `test_geometry.py`: Half-extents, corner formulas, axis-aligned bounds, SAT collision detection, spatial index.
  - `test_contact_lp.py`: HiGHS simplex linear programming compaction and feasibility preservation.
  - `test_pocket_insertion.py`: Pocket void scanning, insertion growth, and diagonal stripe generation.
  - `test_certified_upgrades.py`: Verifies zero overlaps (tolerance 0.0) for all record-breaking layouts.
  - `test_moves.py`: Single translation, rotation, combined moves, group translation, boundary detection.
  - `test_objective.py`: Smooth penalty, container objective, monotonicity.
  - `test_packing.py`: Grid packing, staggered packing, rotated pattern validity.
  - `test_optimization.py`: Simulated annealing, local search, multi-start restart orchestration.
  - `test_integration.py`: Atomic checkpoint writing, corrupted checkpoint recovery, resume semantics.
  - `test_cli.py`: Command-line interface end-to-end execution.

---

## 7. Roadmap to 22.20 & 22.14

1. **GPU Soft-Body Relaxation Sweeps**:
   - Running GPU-accelerated PyTorch relaxation on candidate transition bands ($n \in [50, 500]$) on Kaggle GPU (T4/P100), followed by HiGHS LP contact snapping.
2. **Transition Seam Pattern Search**:
   - Systematic search across diagonal stripe and pocket-insertion patterns for transition puzzles ($n$ immediately preceding square counts), pushing toward **`22.200000`** and the theoretical continuum limit **`22.140000`**.
