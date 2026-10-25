#!/usr/bin/env python
"""Run optimization on a range of puzzles."""

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from squares_in_squares.cli import main

if __name__ == "__main__":
    sys.argv.insert(1, "optimize")
    sys.exit(main())
