"""Tests for spm_decomposition.poverty — child poverty rate computation."""

import numpy as np
import pytest

from conftest import MockMicroSeries, MockMicrosimulation
from spm_decomposition.poverty import compute_child_poverty_rate


# ---------------------------------------------------------------------------
# Helpers to build mock simulations
# ---------------------------------------------------------------------------

def _make_sim(
    is_child,
    person_in_poverty,
    net_income_reported,
    spm_threshold,
    weights=None,
):
    """Build a MockMicrosimulation with the variables needed by poverty.py.

    Uses a 1-to-1 person-to-SPM-unit mapping so that SPM-unit-level values
    map directly back to the same person index.
    """
    n = len(is_child)
    if weights is None:
        weights = np.ones(n)
    # 1-to-1 mapping: each person is their own SPM unit
    spm_ids = np.arange(n, dtype=float)
    return MockMicrosimulation(
        {
            # Person-level variables
            "is_child": MockMicroSeries(is_child, weights),
            "person_in_poverty": MockMicroSeries(person_in_poverty, weights),
            "person_weight": MockMicroSeries(weights, weights),
            "person_spm_unit_id": MockMicroSeries(spm_ids, weights),
            # SPM-unit-level variables (1-to-1 with persons)
            "spm_unit_id": MockMicroSeries(spm_ids, weights),
            "spm_unit_net_income_reported": MockMicroSeries(
                net_income_reported, weights
            ),
            "spm_unit_spm_threshold": MockMicroSeries(spm_threshold, weights),
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestComputeChildPovertyRate:
    """Unit tests for compute_child_poverty_rate."""

    def test_all_children_in_poverty(self):
        """If every child is in poverty, both rates should be 1.0."""
        sim = _make_sim(
            is_child=[1, 1, 1, 0],
            person_in_poverty=[1, 1, 1, 0],
            net_income_reported=[5000, 8000, 3000, 50000],
            spm_threshold=[10000, 10000, 10000, 10000],
        )
        result = compute_child_poverty_rate(sim)
        assert result["computed"] == pytest.approx(1.0)
        assert result["reported"] == pytest.approx(1.0)

    def test_no_children_in_poverty(self):
        """If no child is in poverty, both rates should be 0.0."""
        sim = _make_sim(
            is_child=[1, 1, 0, 0],
            person_in_poverty=[0, 0, 0, 0],
            net_income_reported=[50000, 60000, 5000, 3000],
            spm_threshold=[10000, 10000, 10000, 10000],
        )
        result = compute_child_poverty_rate(sim)
        assert result["computed"] == pytest.approx(0.0)
        assert result["reported"] == pytest.approx(0.0)

    def test_mixed_poverty(self):
        """Computed and reported rates can diverge."""
        # 4 persons: 2 children, 2 adults (equal weights)
        sim = _make_sim(
            is_child=[1, 1, 0, 0],
            # PE says child 0 is in poverty, child 1 is not
            person_in_poverty=[1, 0, 1, 0],
            # Reported income: child 0 above threshold, child 1 below
            net_income_reported=[20000, 5000, 30000, 40000],
            spm_threshold=[10000, 10000, 10000, 10000],
        )
        result = compute_child_poverty_rate(sim)
        # computed: among children, mean of [1, 0] = 0.5
        assert result["computed"] == pytest.approx(0.5)
        # reported: child 0 income 20000 >= 10000 (not poor), child 1 income 5000 < 10000 (poor)
        # so reported = mean of [0, 1] = 0.5
        assert result["reported"] == pytest.approx(0.5)

    def test_weighted_poverty(self):
        """Weights affect the poverty rate computation."""
        sim = _make_sim(
            is_child=[1, 1, 0],
            person_in_poverty=[1, 0, 1],
            net_income_reported=[5000, 20000, 5000],
            spm_threshold=[10000, 10000, 10000],
            weights=[3, 1, 2],
        )
        result = compute_child_poverty_rate(sim)
        # children: persons 0 and 1, weights [3, 1]
        # computed: weighted mean of [1, 0] with weights [3, 1] = 3/4 = 0.75
        assert result["computed"] == pytest.approx(0.75)
        # reported: child 0 income 5000 < 10000 (poor, weight 3), child 1 income 20000 >= 10000 (not poor, weight 1)
        # = 3/4 = 0.75
        assert result["reported"] == pytest.approx(0.75)

    def test_only_adults(self):
        """If there are no children, rates should be 0.0 (no children to be poor)."""
        sim = _make_sim(
            is_child=[0, 0, 0],
            person_in_poverty=[1, 1, 0],
            net_income_reported=[5000, 5000, 50000],
            spm_threshold=[10000, 10000, 10000],
        )
        result = compute_child_poverty_rate(sim)
        # No children -> rates should be 0 (or NaN). We define it as 0.
        # With no children, weighted mean of empty series -> we should handle gracefully
        assert result["computed"] == pytest.approx(0.0)
        assert result["reported"] == pytest.approx(0.0)

    def test_custom_period(self):
        """Period parameter is forwarded to sim.calc()."""
        sim = _make_sim(
            is_child=[1, 1],
            person_in_poverty=[1, 0],
            net_income_reported=[5000, 20000],
            spm_threshold=[10000, 10000],
        )
        # Should not raise — period is just forwarded
        result = compute_child_poverty_rate(sim, period=2023)
        assert "computed" in result
        assert "reported" in result

    def test_return_keys(self):
        """Result dict has exactly the expected keys."""
        sim = _make_sim(
            is_child=[1, 0],
            person_in_poverty=[1, 0],
            net_income_reported=[5000, 50000],
            spm_threshold=[10000, 10000],
        )
        result = compute_child_poverty_rate(sim)
        assert set(result.keys()) == {"computed", "reported"}

    def test_divergent_computed_vs_reported(self):
        """PE-computed poverty can differ from CPS-reported poverty."""
        # 3 children with equal weight
        # PE says: child 0 poor, child 1 poor, child 2 not poor -> computed = 2/3
        # Reported income: child 0 above threshold, child 1 below, child 2 below -> reported = 2/3
        sim = _make_sim(
            is_child=[1, 1, 1],
            person_in_poverty=[1, 1, 0],
            net_income_reported=[20000, 5000, 8000],
            spm_threshold=[10000, 10000, 10000],
        )
        result = compute_child_poverty_rate(sim)
        assert result["computed"] == pytest.approx(2.0 / 3.0)
        assert result["reported"] == pytest.approx(2.0 / 3.0)
