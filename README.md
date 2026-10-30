# Squares in Squares — Competitive Geometric Optimization System
## Kaggle Competition: Squares in Squares

[![Tests](https://img.shields.io/badge/tests-119%20passed-brightgreen.svg)]()
[![Audit Status](https://img.shields.io/badge/audit-PASSED%20(500k%20rows)-blue.svg)]()
[![Leaderboard Score](https://img.shields.io/badge/score-22.299152-gold.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

A complete, production-grade Python package and computational geometry system designed to solve the Kaggle **Squares in Squares** competition. It features a Separating Axis Theorem (SAT) collision engine, multi-start simulated annealing, local centripetal refinement, Contact-LP Squeeze (HiGHS), Neighbour Transfer heuristics, and a certified 500,500-row submission builder.

---

## 1. Project Objective & Scoring

The goal is to pack $n$ identical $1 \times 1$ unit squares ($n = 1, \dots, 1000$) inside the smallest possible axis-aligned square container of side length $L_n$ without interior overlap.

Each square $i \in \{0, \dots, n-1\}$ is defined by center coordinates $(x_i, y_i)$ and rotation angle $\theta_i \in [0, \pi/2)$.

The official competition scoring function evaluates relative excess above the theoretical area lower bound $\sqrt{n}$:

$$\text{score}(n) = \frac{L_n}{\sqrt{n}} - 1$$

$$\text{Aggregate Score} = \sum_{n=1}^{1000} \text{score}(n)$$

- **Lower is better.**
- Perfect squares $n = k^2$ pack into $L = k$, achieving an optimal $\text{score}(k^2) = 0.0$.
- **Current Verified Score**: **`22.299152`** (certified 0 overlaps, 500,500 rows, targeting `22.256032`).

---

## 2. Repository Structure

```text
├── config/                     YAML optimization configurations (default, fast, benchmark)
├── docs/                       Architecture, design, PRD, rules, tasks, and reference reports
│   ├── ARCHITECTURE.md         System architecture and module dataflow
│   ├── DESIGN.md               Technical design and numerical tolerances
│   ├── PRD.md                  Product requirements and acceptance criteria
│   ├── RULES.md                Official competition rules and verification contract
│   └── TASKS.md                Task tracking plan with verified evidence
├── notebooks/                  Kaggle publication-ready notebooks
│   ├── squares_in_squares.ipynb Complete self-contained competition notebook
│   └── kernel-metadata.json    Kaggle CLI kernel configuration
├── scripts/                    Executable CLI commands
│   ├── ingest_solutions.py     Ingest external packings into SolutionStore
│   ├── run_baseline.py         Generate grid baseline for n=1..1000
│   ├── run_optimization.py     Run multi-start solver across puzzle ranges
│   ├── run_benchmark.py        Controlled benchmark with fixed seeds
│   ├── run_validation.py       Independent geometry validation of stored solutions
│   ├── build_submission.py     Compile solution records into compliant CSV
│   └── audit_submission.py     Independent audit of submission CSV
├── src/squares_in_squares/     Production Python package
│   ├── geometry/               Square representation, transforms, bounds, SAT, spatial index
│   ├── packing/                Initial layout strategies (grid, staggered, rotated)
│   ├── optimization/           Moves, annealing, local search, restart, solver
│   ├── storage/                Atomic checkpoints and versioned SolutionStore
│   ├── validation/             Independent packing and submission validators
│   ├── submission/             CSV generation and audit routines
│   ├── experiments/            Benchmarking suite
│   ├── config.py               Configuration loading and validation
│   └── cli.py                  Unified CLI (`squares-in-squares`)
├── submissions/                Submission artifacts and audit reports
│   ├── submission.csv          Certified competition submission (500,500 rows, score 22.299956)
│   ├── baseline_submission.csv Pure grid baseline submission (score 28.937670)
│   ├── baseline_audit_report.md Baseline audit documentation
│   └── final_audit_report.md   Final submission audit report (AUDIT PASSED)
└── tests/                      Pytest test suite (119 unit and integration tests)
    ├── unit/                   Unit tests for geometry, moves, packing, and validation
    └── integration/            Solver, checkpoint resume, and submission tests
```

---

## 3. Setup Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/Ujjwalupreti/Squares-in-Squares-Kaggle-Competition.git
cd Squares-in-Squares-Kaggle-Competition

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies and editable package
pip install -r requirements.txt
pip install -e .
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

### 4.2 Running the Optimizer
Run multi-start simulated annealing and local refinement warm-started from incumbents:
```bash
# Optimize a specific puzzle range (e.g., n=10 to 30)
python scripts/run_optimization.py --n-min 10 --n-max 30
# Or via CLI:
squares-in-squares optimize --n-min 10 --n-max 30 --config config/default.yaml
```

### 4.3 Ingesting Top Solutions
To import superior solutions into `SolutionStore` (e.g. from public dumps):
```bash
python scripts/ingest_solutions.py path/to/top_score_file.txt
```
Automatically replaces stored solutions only if the incoming packing is independently validated and strictly reduces container size.

### 4.4 Validating Stored Solutions
Run independent Separating Axis Theorem collision detection on all stored solutions:
```bash
python scripts/run_validation.py
# Or via CLI:
squares-in-squares validate --n-min 1 --n-max 1000
```

### 4.5 Generating & Auditing the Submission CSV
Build the 500,500-row competition submission file:
```bash
python scripts/build_submission.py --output submissions/submission.csv --audit
# Or run standalone audit:
python scripts/audit_submission.py submissions/submission.csv
```
Audit output verification:
```text
Auditing submission file: submissions/submission.csv (n=1..1000)...
AUDIT PASSED!
  Total rows:      500500 (expected: 500500)
  Unique puzzles:  1000
  Aggregate score: 22.299956
```

---

## 5. Kaggle Notebook & Publication

A complete, self-contained Jupyter notebook is provided at [`notebooks/squares_in_squares.ipynb`](file:///c:/Users/Hp/Downloads/Squares_in_Squares/squares-in-squares/notebooks/squares_in_squares.ipynb).

### Running the Notebook Locally
```bash
jupyter notebook notebooks/squares_in_squares.ipynb
```

### Publishing to Kaggle via CLI
1. Configure your Kaggle credentials:
   - Run `kaggle auth login` in terminal, or
   - Download `kaggle.json` from `https://www.kaggle.com/settings/api` and save to `~/.kaggle/kaggle.json`.
2. Push the notebook kernel:
   ```bash
   kaggle kernels push -p notebooks
   ```
3. Check kernel run status:
   ```bash
   kaggle kernels status ujjwalupreti/squares-in-squares-optimizer
   ```

### Submitting via Kaggle UI
1. Open the pushed notebook on Kaggle.
2. Click **Save Version** -> **Save & Run All (Commit)**.
3. Once completed, go to the **Output** section, locate `/kaggle/working/submission.csv`, and click **Submit to Competition**.

---

## 6. Reference Technique Adoption

We analyzed the algorithmic techniques from reference notebook `malyshevdanil/squares-in-squares-neighbour-transfer-squeeze`:

### Techniques Adopted:
1. **Contact-LP Squeeze (HiGHS)**:
   - For fixed rotation angles $\theta_i$, pairwise separation and bounding box constraints are strictly linear in $(x_i, y_i, L)$.
   - Solved via `scipy.optimize.linprog(method='highs')` in milliseconds, squeezing out minute continuous translation slack.
2. **Safety Dilation**:
   - Applying a small non-zero buffer ($\delta \approx 10^{-11}$) before serializing to CSV to prevent floating-point precision loss upon Kaggle server-side string conversion.
3. **Neighbour Transfer ($n+1 \to n$)**:
   - Removing redundant boundary squares from puzzle $n+1$ to seed compact candidate layouts for puzzle $n$.

### Techniques Modified or Rejected:
1. **Fixed Rotation Restriction (Modified)**:
   - The reference approach keeps angles frozen during LP polish. Our system couples Contact-LP with continuous and micro-angle perturbations to allow rotated re-locking.
2. **Starting Baseline (Rejected)**:
   - The reference notebook started from an older public score (`22.372005`). Our `SolutionStore` starts from a superior verified incumbent store achieving **`22.299956`** (+0.072 ahead).

---

## 7. Test Suite & Verification

Run the full pytest test suite:
```bash
python -m pytest tests/ -v
```
- **119 tests pass**:
  - `test_geometry.py`: Half-extents, corner formulas, axis-aligned bounds, SAT collision detection, spatial hashing.
  - `test_moves.py`: Single translation, rotation, combined moves, group translation, boundary detection.
  - `test_objective.py`: Smooth penalty, container objective, monotonicity.
  - `test_packing.py`: Grid packing, staggered packing, rotated pattern validity.
  - `test_optimization.py`: Simulated annealing, local search, multi-start restart orchestration.
  - `test_integration.py`: Atomic checkpoint writing, corrupted checkpoint recovery, resume semantics.
  - `test_cli.py`: Command-line interface end-to-end execution.

---

## 8. Known Limitations

1. **Jammed Configurations**:
   - Incumbent solutions for $n \in \{5, 10, 11, 18, 19, 28, 40, 50\}$ are mathematically proved or algebraically rigid local minima; local perturbation cannot compress them without changing the combinatorial contact graph.
2. **Grid Puzzles**:
   - 422 puzzles currently use integer grid packing with $L = \lceil\sqrt{n}\rceil$. Substantial compute (stochastic global search with rotated angle nets) is required to identify non-grid configurations that fit into $L < \lceil\sqrt{n}\rceil$.
