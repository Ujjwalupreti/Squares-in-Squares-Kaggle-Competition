# Kaggle Setup and GitHub Workflow Guide
## Kaggle Squares in Squares Optimization System

This guide explains how to deploy, execute, and persist solutions when running on Kaggle Notebooks and synchronizing with GitHub.

---

## 1. Architecture on Kaggle

Kaggle provides ephemeral CPU (and GPU) environments with:
- `/kaggle/working`: The persistent output directory preserved in notebook output.
- Ephemeral runtime: Sessions reset after inactivity or when GPU/CPU limits expire (typically 9–12 hours).
- Internet access: Must be enabled in notebook settings to clone GitHub repositories or pip-install packages.

### Recommended Directory Structure on Kaggle
```text
/kaggle/working/
  checkpoints/            # Intermediate checkpoints saved every N iterations
  artifacts/
    solutions/            # Best-valid-solution JSONs (solution_n0001.json .. solution_n1000.json)
    benchmark_log.jsonl   # Append-only experiment metrics log
  submissions/
    submission.csv        # Final 500,500-row competition submission file
    baseline_submission.csv
```

---

## 2. GitHub Workflow

1. **Version Control**:
   - Commit and push code updates to your GitHub repository.
   - Do NOT commit large generated files (`.csv`, checkpoints, thousands of JSONs) to Git. The `.gitignore` is pre-configured to exclude `artifacts/`, `checkpoints/`, `submissions/`, and python caches.

2. **Kaggle Linking**:
   - In Kaggle Notebook settings, link your GitHub repository OR clone directly:
   ```bash
   !git clone https://github.com/<your-username>/Squares_in_Squares.git
   %cd Squares_in_Squares/squares-in-squares
   ```

---

## 3. Environment Installation on Kaggle

Run the following cell at the beginning of your Kaggle notebook:

```python
import sys
import subprocess

# Install package in editable or standard mode
subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
```

Verify tests before starting long runs:
```bash
!pytest tests/unit/ -v --tb=short
!pytest tests/integration/ -v --tb=short
```

---

## 4. Execution Workflow

### Step 1: Generate Guaranteed-Feasible Baseline
To immediately secure a valid complete submission (all 1,000 puzzles):
```bash
python scripts/run_baseline.py --n-min 1 --n-max 1000
```
This writes `solution_n0001.json` through `solution_n1000.json` into `artifacts/solutions/`.

### Step 2: Build & Audit Baseline Submission
```bash
python scripts/build_submission.py --output /kaggle/working/submissions/baseline_submission.csv --audit
```
This confirms:
- Exact 500,500 row count.
- Unique sequential `id` from 0 to 500,499.
- Columns: `id,n,square_id,x,y,angle`.
- No NaN, inf, or pairwise overlaps.

### Step 3: Run Optimization Search
Run optimization over a target range of puzzles:
```bash
# Example: optimize puzzles 2 through 50 with benchmark config
python scripts/run_optimization.py -c config/benchmark.yaml --n-min 2 --n-max 50
```

### Step 4: Checkpointing & Resuming
- The optimization engine uses atomic writes for checkpoints.
- Solutions in `artifacts/solutions/` are only overwritten if the new score is strictly better than the stored incumbent.
- In Kaggle, save output datasets periodically so progress is preserved across sessions.

### Step 5: Final Audit & Submission
Before submitting to Kaggle:
```bash
python scripts/build_submission.py --output /kaggle/working/submission.csv --audit
```
Ensure the final report displays `AUDIT PASSED!`.
