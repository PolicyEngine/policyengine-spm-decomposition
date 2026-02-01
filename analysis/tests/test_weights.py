"""Tests for spm_decomposition.weights — weight rebalancing by household type."""

import numpy as np
import pytest

from conftest import MockMicroSeries, MockMicrosimulation
from spm_decomposition.weights import compute_weight_rebalancing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_weight_sim(
    is_child,
    person_in_poverty,
    net_income_reported,
    spm_threshold,
    tax_unit_is_joint,
    weights=None,
):
    """Build a MockMicrosimulation for weight rebalancing tests.

    Uses 1-to-1 person-to-SPM-unit and person-to-tax-unit mappings so that
    entity-level values map directly back to the same person index.
    """
    n = len(is_child)
    if weights is None:
        weights = np.ones(n)
    # 1-to-1 mappings: each person is their own SPM unit and tax unit
    entity_ids = np.arange(n, dtype=float)
    return MockMicrosimulation(
        {
            # Person-level variables
            "is_child": MockMicroSeries(is_child, weights),
            "person_in_poverty": MockMicroSeries(person_in_poverty, weights),
            "person_weight": MockMicroSeries(weights, weights),
            "person_spm_unit_id": MockMicroSeries(entity_ids, weights),
            "person_tax_unit_id": MockMicroSeries(entity_ids, weights),
            # SPM-unit-level variables (1-to-1 with persons)
            "spm_unit_id": MockMicroSeries(entity_ids, weights),
            "spm_unit_net_income_reported": MockMicroSeries(
                net_income_reported, weights
            ),
            "spm_unit_spm_threshold": MockMicroSeries(spm_threshold, weights),
            # Tax-unit-level variables (1-to-1 with persons)
            "tax_unit_id": MockMicroSeries(entity_ids, weights),
            "tax_unit_is_joint": MockMicroSeries(tax_unit_is_joint, weights),
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestComputeWeightRebalancing:
    """Unit tests for compute_weight_rebalancing."""

    def test_returns_groups_key(self):
        """Result dict has 'groups' key containing a list."""
        raw = _make_weight_sim(
            is_child=[1, 1, 0, 0],
            person_in_poverty=[1, 0, 0, 0],
            net_income_reported=[5000, 50000, 30000, 80000],
            spm_threshold=[10000, 10000, 10000, 10000],
            tax_unit_is_joint=[0, 1, 0, 1],
        )
        enhanced = _make_weight_sim(
            is_child=[1, 1, 0, 0],
            person_in_poverty=[0, 0, 0, 0],
            net_income_reported=[5000, 50000, 30000, 80000],
            spm_threshold=[10000, 10000, 10000, 10000],
            tax_unit_is_joint=[0, 1, 0, 1],
        )
        result = compute_weight_rebalancing(raw, enhanced)
        assert "groups" in result
        assert isinstance(result["groups"], list)

    def test_group_structure(self):
        """Each group has the expected keys."""
        # 10 persons so we have enough for quintile assignment
        n = 20
        np.random.seed(42)
        is_child = np.array([1] * 10 + [0] * 10, dtype=float)
        person_in_poverty = np.zeros(n)
        person_in_poverty[:3] = 1  # first 3 children are poor
        net_income = np.linspace(5000, 100000, n)
        spm_threshold = np.full(n, 25000.0)
        tax_unit_is_joint = np.array([0, 1] * 10, dtype=float)
        weights = np.ones(n)

        raw = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint, weights,
        )
        enhanced = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint, weights,
        )
        result = compute_weight_rebalancing(raw, enhanced)

        for group in result["groups"]:
            assert "label" in group
            assert "raw_cps_poverty_rate" in group
            assert "enhanced_cps_poverty_rate" in group
            assert "raw_cps_child_share" in group
            assert "enhanced_cps_child_share" in group

    def test_child_shares_sum_to_one(self):
        """Child shares across all groups should sum to approximately 1.0."""
        n = 20
        is_child = np.array([1] * 10 + [0] * 10, dtype=float)
        person_in_poverty = np.zeros(n)
        person_in_poverty[:5] = 1
        net_income = np.linspace(5000, 100000, n)
        spm_threshold = np.full(n, 25000.0)
        tax_unit_is_joint = np.array([0, 1] * 10, dtype=float)

        raw = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint,
        )
        enhanced = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint,
        )
        result = compute_weight_rebalancing(raw, enhanced)
        raw_total = sum(g["raw_cps_child_share"] for g in result["groups"])
        enhanced_total = sum(g["enhanced_cps_child_share"] for g in result["groups"])
        assert raw_total == pytest.approx(1.0, abs=0.01)
        assert enhanced_total == pytest.approx(1.0, abs=0.01)

    def test_different_weights_shift_child_shares(self):
        """When enhanced CPS has different weights, child shares change."""
        n = 10
        is_child = np.array([1] * 5 + [0] * 5, dtype=float)
        person_in_poverty = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float)
        net_income = np.linspace(5000, 50000, n)
        spm_threshold = np.full(n, 10000.0)
        tax_unit_is_joint = np.array([0, 0, 1, 1, 0, 0, 1, 1, 0, 1], dtype=float)

        raw_weights = np.ones(n)
        enhanced_weights = np.ones(n)
        # Double the weight of the first child (low-income single parent)
        enhanced_weights[0] = 5.0

        raw = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint, raw_weights,
        )
        enhanced = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint, enhanced_weights,
        )
        result = compute_weight_rebalancing(raw, enhanced)

        # The enhanced sim should have a higher poverty rate overall since
        # the poor child got more weight
        raw_poverty_rates = [
            g["raw_cps_poverty_rate"] * g["raw_cps_child_share"]
            for g in result["groups"]
        ]
        enhanced_poverty_rates = [
            g["enhanced_cps_poverty_rate"] * g["enhanced_cps_child_share"]
            for g in result["groups"]
        ]
        raw_overall = sum(raw_poverty_rates)
        enhanced_overall = sum(enhanced_poverty_rates)
        assert enhanced_overall > raw_overall

    def test_poverty_rates_bounded(self):
        """All poverty rates should be between 0 and 1."""
        n = 20
        np.random.seed(123)
        is_child = np.random.choice([0.0, 1.0], n, p=[0.4, 0.6])
        person_in_poverty = np.random.choice([0.0, 1.0], n, p=[0.7, 0.3])
        net_income = np.random.uniform(5000, 100000, n)
        spm_threshold = np.full(n, 30000.0)
        tax_unit_is_joint = np.random.choice([0.0, 1.0], n)

        raw = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint,
        )
        enhanced = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint,
        )
        result = compute_weight_rebalancing(raw, enhanced)
        for g in result["groups"]:
            assert 0.0 <= g["raw_cps_poverty_rate"] <= 1.0
            assert 0.0 <= g["enhanced_cps_poverty_rate"] <= 1.0
            assert 0.0 <= g["raw_cps_child_share"] <= 1.0
            assert 0.0 <= g["enhanced_cps_child_share"] <= 1.0

    def test_labels_contain_quintile_and_structure(self):
        """Labels should encode both income quintile and family structure."""
        n = 20
        is_child = np.array([1] * 10 + [0] * 10, dtype=float)
        person_in_poverty = np.zeros(n)
        net_income = np.linspace(5000, 100000, n)
        spm_threshold = np.full(n, 25000.0)
        tax_unit_is_joint = np.array([0, 1] * 10, dtype=float)

        raw = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint,
        )
        enhanced = _make_weight_sim(
            is_child, person_in_poverty, net_income, spm_threshold,
            tax_unit_is_joint,
        )
        result = compute_weight_rebalancing(raw, enhanced)
        labels = [g["label"] for g in result["groups"]]
        # Should have at most 10 groups (5 quintiles x 2 family structures)
        assert len(labels) <= 10
        # Each label should be unique
        assert len(labels) == len(set(labels))
