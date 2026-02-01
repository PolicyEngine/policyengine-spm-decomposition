"""Tests for spm_decomposition.decomposition — the orchestrator."""

import numpy as np
import pytest

from conftest import MockMicroSeries, MockMicrosimulation
from spm_decomposition.decomposition import run_decomposition


# ---------------------------------------------------------------------------
# Helpers: build consistent mock sims with ALL required variables
# ---------------------------------------------------------------------------

def _full_mock_sim(
    n=50,
    seed=42,
    poverty_rate_approx=0.20,
    tax_rate=0.20,
    tax_reported_rate=0.18,
):
    """Build a MockMicrosimulation with every variable the orchestrator needs.

    This creates a synthetic dataset of ``n`` persons (half children, half
    adults) with controllable poverty and tax rates.
    """
    rng = np.random.RandomState(seed)

    is_child = np.array([1.0] * (n // 2) + [0.0] * (n - n // 2))
    weights = rng.uniform(1.0, 5.0, n)

    # Income
    income = rng.uniform(5000, 150000, n)
    spm_threshold = np.full(n, 30000.0)

    # PE-computed poverty
    person_in_poverty = np.zeros(n)
    n_poor = int(n * poverty_rate_approx)
    poor_idx = rng.choice(n, size=n_poor, replace=False)
    person_in_poverty[poor_idx] = 1.0

    # Tax variables (tax-unit level, but mock treats everything as person-level)
    agi = income.copy()
    income_tax = agi * tax_rate
    income_tax_reported = agi * tax_reported_rate

    # Family structure
    tax_unit_is_joint = rng.choice([0.0, 1.0], n)

    return MockMicrosimulation(
        {
            "is_child": MockMicroSeries(is_child, weights),
            "person_in_poverty": MockMicroSeries(person_in_poverty, weights),
            "spm_unit_net_income_reported": MockMicroSeries(income, weights),
            "spm_unit_spm_threshold": MockMicroSeries(spm_threshold, weights),
            "adjusted_gross_income": MockMicroSeries(agi, weights),
            "income_tax": MockMicroSeries(income_tax, weights),
            "income_tax_reported": MockMicroSeries(income_tax_reported, weights),
            "tax_unit_is_joint": MockMicroSeries(tax_unit_is_joint, weights),
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRunDecomposition:
    """Unit tests for run_decomposition (mocked, no real PE data)."""

    def test_returns_dict(self, monkeypatch):
        """Orchestrator returns a JSON-serializable dict."""
        raw_sim = _full_mock_sim(seed=1)
        enh_sim = _full_mock_sim(seed=2)

        # Patch Microsimulation loading and state computation
        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_raw_cps_sim",
            lambda: raw_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_enhanced_cps_sim",
            lambda: enh_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition.compute_state_results",
            lambda period=2024: [],
        )
        result = run_decomposition()
        assert isinstance(result, dict)

    def test_top_level_keys(self, monkeypatch):
        """Result has the expected top-level keys."""
        raw_sim = _full_mock_sim(seed=10)
        enh_sim = _full_mock_sim(seed=20)

        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_raw_cps_sim",
            lambda: raw_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_enhanced_cps_sim",
            lambda: enh_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition.compute_state_results",
            lambda period=2024: [],
        )
        result = run_decomposition()

        expected_keys = {
            "census_benchmark",
            "raw_cps_poverty",
            "enhanced_cps_poverty",
            "weight_rebalancing",
            "raw_cps_tax_gap",
            "enhanced_cps_tax_gap",
            "waterfall",
            "state_results",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_waterfall_structure(self, monkeypatch):
        """Waterfall is a list of step dicts with label and value."""
        raw_sim = _full_mock_sim(seed=30)
        enh_sim = _full_mock_sim(seed=40)

        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_raw_cps_sim",
            lambda: raw_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_enhanced_cps_sim",
            lambda: enh_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition.compute_state_results",
            lambda period=2024: [],
        )
        result = run_decomposition()

        waterfall = result["waterfall"]
        assert isinstance(waterfall, list)
        assert len(waterfall) >= 3  # at least Census, raw CPS reported, raw CPS computed
        for step in waterfall:
            assert "label" in step
            assert "value" in step

    def test_census_benchmark_value(self, monkeypatch):
        """Census benchmark should match config constant."""
        raw_sim = _full_mock_sim(seed=50)
        enh_sim = _full_mock_sim(seed=60)

        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_raw_cps_sim",
            lambda: raw_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_enhanced_cps_sim",
            lambda: enh_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition.compute_state_results",
            lambda period=2024: [],
        )
        result = run_decomposition()
        assert result["census_benchmark"] == pytest.approx(0.134)

    def test_poverty_dicts_have_computed_and_reported(self, monkeypatch):
        """Poverty results should have computed and reported keys."""
        raw_sim = _full_mock_sim(seed=70)
        enh_sim = _full_mock_sim(seed=80)

        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_raw_cps_sim",
            lambda: raw_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_enhanced_cps_sim",
            lambda: enh_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition.compute_state_results",
            lambda period=2024: [],
        )
        result = run_decomposition()

        for key in ["raw_cps_poverty", "enhanced_cps_poverty"]:
            assert "computed" in result[key]
            assert "reported" in result[key]

    def test_tax_gap_has_10_deciles(self, monkeypatch):
        """Tax gap results should have 10 decile entries each."""
        raw_sim = _full_mock_sim(n=100, seed=90)
        enh_sim = _full_mock_sim(n=100, seed=100)

        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_raw_cps_sim",
            lambda: raw_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_enhanced_cps_sim",
            lambda: enh_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition.compute_state_results",
            lambda period=2024: [],
        )
        result = run_decomposition()
        assert len(result["raw_cps_tax_gap"]) == 10
        assert len(result["enhanced_cps_tax_gap"]) == 10

    def test_json_serializable(self, monkeypatch):
        """Full result should be JSON-serializable."""
        import json

        raw_sim = _full_mock_sim(seed=110)
        enh_sim = _full_mock_sim(seed=120)

        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_raw_cps_sim",
            lambda: raw_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition._load_enhanced_cps_sim",
            lambda: enh_sim,
        )
        monkeypatch.setattr(
            "spm_decomposition.decomposition.compute_state_results",
            lambda period=2024: [],
        )
        result = run_decomposition()
        # Should not raise
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
