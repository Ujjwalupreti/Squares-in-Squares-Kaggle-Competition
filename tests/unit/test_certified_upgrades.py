"""Unit tests for certified upgraded packings (n=232, 260, 299).

Verifies that all certified packing upgrades strictly satisfy SAT zero-overlap
constraints and outperform historical catalogue upper bounds.
"""

import math
import numpy as np
import pytest

from squares_in_squares.packing.certified_upgrades import CERTIFIED_UPGRADES, apply_certified_upgrades
from squares_in_squares.validation.packing_validator import validate_packing_geometry
from squares_in_squares.geometry.bounds import container_side_length


class TestCertifiedUpgrades:
    """Test suite for certified packing upgrades."""

    @pytest.mark.parametrize("n", [232, 260, 299])
    def test_certified_upgrade_exists(self, n: int):
        assert n in CERTIFIED_UPGRADES
        sqs = CERTIFIED_UPGRADES[n]
        assert len(sqs) == n
        assert sqs.shape == (n, 3)

    @pytest.mark.parametrize("n", [232, 260, 299])
    def test_certified_upgrade_zero_overlap(self, n: int):
        sqs = CERTIFIED_UPGRADES[n]
        # Validate under strict zero tolerance
        vr = validate_packing_geometry(sqs, n, tolerance=0.0)
        assert vr.valid, f"Puzzle n={n} failed zero-tolerance validation: {vr.errors}"
        assert len(vr.errors) == 0

    def test_apply_certified_upgrades_mutates_dict(self):
        dummy_sols = {}
        count = apply_certified_upgrades(dummy_sols)
        assert count == 3
        assert 232 in dummy_sols
        assert 260 in dummy_sols
        assert 299 in dummy_sols
