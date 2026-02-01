"""Tests for spm_decomposition.tax_gap — federal tax gap by income decile."""

import numpy as np
import pytest

from conftest import MockMicroSeries, MockMicrosimulation
from spm_decomposition.tax_gap import compute_tax_gap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tax_sim(
    spm_unit_total_income_reported,
    spm_unit_federal_tax,
    spm_unit_federal_tax_reported,
    weights=None,
):
    """Build a MockMicrosimulation for tax gap tests.

    All variables are at the SPM-unit level. The production code accesses
    the ``.weights`` property on the MicroSeries returned by
    ``sim.calc("spm_unit_total_income_reported", ...)``.
    """
    n = len(spm_unit_total_income_reported)
    if weights is None:
        weights = np.ones(n)
    return MockMicrosimulation(
        {
            "spm_unit_total_income_reported": MockMicroSeries(
                spm_unit_total_income_reported, weights
            ),
            "spm_unit_federal_tax": MockMicroSeries(
                spm_unit_federal_tax, weights
            ),
            "spm_unit_federal_tax_reported": MockMicroSeries(
                spm_unit_federal_tax_reported, weights
            ),
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestComputeTaxGap:
    """Unit tests for compute_tax_gap."""

    def test_returns_list_of_10_dicts(self):
        """Result is a list of exactly 10 decile dicts."""
        n = 100
        np.random.seed(42)
        agi = np.linspace(10000, 500000, n)
        tax_pe = agi * 0.20
        tax_reported = agi * 0.18
        sim = _make_tax_sim(agi, tax_pe, tax_reported)
        result = compute_tax_gap(sim)
        assert isinstance(result, list)
        assert len(result) == 10

    def test_decile_keys(self):
        """Each decile dict has the expected keys."""
        n = 100
        agi = np.linspace(10000, 500000, n)
        sim = _make_tax_sim(agi, agi * 0.2, agi * 0.18)
        result = compute_tax_gap(sim)
        for d in result:
            assert "decile" in d
            assert "mean_income" in d
            assert "pe_federal_tax" in d
            assert "reported_federal_tax" in d
            assert "gap" in d

    def test_gap_equals_pe_minus_reported(self):
        """Gap should equal PE tax minus reported tax for each decile."""
        n = 100
        agi = np.linspace(10000, 500000, n)
        tax_pe = agi * 0.22
        tax_reported = agi * 0.18
        sim = _make_tax_sim(agi, tax_pe, tax_reported)
        result = compute_tax_gap(sim)
        for d in result:
            assert d["gap"] == pytest.approx(
                d["pe_federal_tax"] - d["reported_federal_tax"], abs=0.01
            )

    def test_zero_gap_when_taxes_match(self):
        """If PE and reported taxes are identical, gap should be zero."""
        n = 50
        agi = np.linspace(20000, 200000, n)
        tax = agi * 0.15
        sim = _make_tax_sim(agi, tax, tax)
        result = compute_tax_gap(sim)
        for d in result:
            assert d["gap"] == pytest.approx(0.0, abs=0.01)

    def test_mean_income_increases_across_deciles(self):
        """Mean income should generally increase from decile 1 to 10."""
        n = 200
        np.random.seed(99)
        agi = np.random.uniform(10000, 500000, n)
        sim = _make_tax_sim(agi, agi * 0.2, agi * 0.18)
        result = compute_tax_gap(sim)
        incomes = [d["mean_income"] for d in result]
        # Income should be monotonically non-decreasing across deciles
        for i in range(len(incomes) - 1):
            assert incomes[i] <= incomes[i + 1]

    def test_decile_labels(self):
        """Deciles should be labeled 1 through 10."""
        n = 100
        agi = np.linspace(10000, 500000, n)
        sim = _make_tax_sim(agi, agi * 0.2, agi * 0.18)
        result = compute_tax_gap(sim)
        decile_labels = [d["decile"] for d in result]
        assert decile_labels == list(range(1, 11))

    def test_weighted_tax_gap(self):
        """Weights should affect the mean computations."""
        # 4 tax units: 2 low income, 2 high income
        agi = np.array([10000, 10000, 100000, 100000])
        tax_pe = np.array([1000, 1000, 25000, 25000])
        tax_reported = np.array([800, 800, 20000, 20000])
        # Give high-income units much more weight
        weights = np.array([1, 1, 10, 10])
        sim = _make_tax_sim(agi, tax_pe, tax_reported, weights)
        result = compute_tax_gap(sim)
        # Just verify it runs and returns 10 deciles
        assert len(result) == 10

    def test_custom_period(self):
        """Period parameter is forwarded without error."""
        n = 20
        agi = np.linspace(10000, 200000, n)
        sim = _make_tax_sim(agi, agi * 0.2, agi * 0.18)
        result = compute_tax_gap(sim, period=2023)
        assert len(result) == 10
