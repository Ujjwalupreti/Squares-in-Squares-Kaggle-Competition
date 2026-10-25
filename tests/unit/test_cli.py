"""Unit tests for configuration loading and CLI."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
import pytest

from squares_in_squares.config import Config
from squares_in_squares.cli import (
    cmd_baseline,
    cmd_validate,
    cmd_submit,
    cmd_audit,
)


class TestConfig:
    """Test suite for configuration loading and validation."""

    def test_default_config(self):
        cfg = Config.default()
        assert cfg.n_min == 1
        assert cfg.n_max == 1000
        assert cfg.sa_initial_temp > 0
        assert 0 < cfg.sa_cooling_rate < 1
        assert cfg.sat_tolerance > 0

    def test_config_from_yaml(self, tmp_path: Path):
        yaml_content = """
n_min: 5
n_max: 20
sa_initial_temp: 2.5
sa_cooling_rate: 0.95
sa_min_temp: 1.0e-5
sa_max_iterations: 500
random_seed: 99
"""
        cfg_file = tmp_path / "test_config.yaml"
        cfg_file.write_text(yaml_content)

        cfg = Config.from_yaml(cfg_file)
        assert cfg.n_min == 5
        assert cfg.n_max == 20
        assert cfg.sa_initial_temp == 2.5
        assert cfg.sa_cooling_rate == 0.95
        assert cfg.random_seed == 99

    def test_invalid_config_raises(self):
        with pytest.raises(ValueError):
            Config(n_min=10, n_max=5)  # n_min > n_max
        with pytest.raises(ValueError):
            Config(sa_initial_temp=-1.0)
        with pytest.raises(ValueError):
            Config(sa_cooling_rate=1.5)


class TestCLICommands:
    """Test suite for CLI command dispatch."""

    def test_cli_baseline_and_validate(self, tmp_path: Path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(f"""
n_min: 1
n_max: 3
solutions_dir: "{tmp_path.as_posix()}/solutions"
submissions_dir: "{tmp_path.as_posix()}/submissions"
artifacts_dir: "{tmp_path.as_posix()}/artifacts"
checkpoints_dir: "{tmp_path.as_posix()}/checkpoints"
""")

        # Run baseline for n=1..3
        args_base = argparse.Namespace(
            config=str(cfg_file),
            n_min=1,
            n_max=3,
        )
        assert cmd_baseline(args_base) == 0

        # Validate stored solutions
        args_val = argparse.Namespace(
            config=str(cfg_file),
            n_min=1,
            n_max=3,
        )
        assert cmd_validate(args_val) == 0

        # Submit and audit
        sub_csv = tmp_path / "submission.csv"
        args_sub = argparse.Namespace(
            config=str(cfg_file),
            output=str(sub_csv),
            n_min=1,
            n_max=3,
            audit=True,
        )
        assert cmd_submit(args_sub) == 0
        assert sub_csv.exists()

        # Audit directly
        args_audit = argparse.Namespace(
            config=str(cfg_file),
            csv=str(sub_csv),
            n_min=1,
            n_max=3,
        )
        assert cmd_audit(args_audit) == 0
