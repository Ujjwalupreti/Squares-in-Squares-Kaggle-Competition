"""Unit tests for Contact-LP Squeeze optimizer."""

import math
import numpy as np
import pytest

from squares_in_squares.optimization.contact_lp import (
    contact_lp_squeeze,
    get_separating_axis_constraint,
)
from squares_in_squares.geometry.bounds import container_side_length
from squares_in_squares.validation.packing_validator import validate_packing_geometry


class TestContactLP:
    def test_separating_axis_axis_aligned(self):
        """Separating axis between two axis-aligned squares."""
        ax, ay, req = get_separating_axis_constraint(0.5, 0.5, 0.0, 1.6, 0.5, 0.0)
        assert abs(ax) > 0.9
        assert abs(ay) < 0.1
        assert req == pytest.approx(1.0, abs=1e-5)

    def test_contact_lp_on_n5_göbel(self):
        """Contact LP on n=5 Göbel layout recovers tight positive clearance."""
        eps = 1e-6
        L5 = 2.0 + 1.0 / math.sqrt(2.0) + eps
        sq = np.array([
            [0.5, 0.5, 0.0],
            [L5 - 0.5, 0.5, 0.0],
            [0.5, L5 - 0.5, 0.0],
            [L5 - 0.5, L5 - 0.5, 0.0],
            [L5 / 2.0, L5 / 2.0, math.pi / 4.0],
        ], dtype=np.float64)

        compacted, new_L, improved = contact_lp_squeeze(sq, 5, safety_margin=1e-10)
        vr = validate_packing_geometry(compacted, 5)
        assert vr.valid
        assert new_L <= L5

    def test_contact_lp_preserves_feasibility(self):
        """Contact LP must never produce overlapping configurations."""
        # 4 unit squares arranged loosely in 3x3 container
        sq = np.array([
            [0.6, 0.6, 0.0],
            [2.2, 0.6, 0.0],
            [0.6, 2.2, 0.0],
            [2.2, 2.2, 0.0],
        ], dtype=np.float64)
        orig_L = container_side_length(sq)

        compacted, new_L, improved = contact_lp_squeeze(sq, 4, safety_margin=1e-10)
        vr = validate_packing_geometry(compacted, 4)
        assert vr.valid
        if improved:
            assert new_L < orig_L

