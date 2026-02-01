"""Orchestrator: run full SPM child poverty decomposition pipeline."""

from .config import (
    CENSUS_PUBLISHED_CHILD_POVERTY_2024,
    ENHANCED_CPS_DATASET,
    RAW_CPS_DATASET,
    YEAR,
)
from .poverty import compute_child_poverty_rate
from .weights import compute_weight_rebalancing
from .tax_gap import compute_tax_gap
from .states import compute_state_results


# ---------------------------------------------------------------------------
# Dataset loaders (thin wrappers so tests can monkeypatch them)
# ---------------------------------------------------------------------------


def _load_raw_cps_sim():
    """Load raw CPS microsimulation from HuggingFace."""
    from policyengine_us import Microsimulation

    return Microsimulation(dataset=RAW_CPS_DATASET)


def _load_enhanced_cps_sim():
    """Load enhanced CPS microsimulation from HuggingFace."""
    from policyengine_us import Microsimulation

    return Microsimulation(dataset=ENHANCED_CPS_DATASET)


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def run_decomposition(period=YEAR) -> dict:
    """Run the full SPM child poverty decomposition.

    This is the main entry point.  It:
    1. Loads raw and enhanced CPS microsimulations.
    2. Computes child poverty rates (PE-computed and CPS-reported) on both.
    3. Computes weight rebalancing analysis (quintile x family structure).
    4. Computes federal tax gap by income decile on both datasets.
    5. Computes state-level results.
    6. Builds the waterfall decomposition.

    Returns
    -------
    dict
        JSON-serializable result with all decomposition data.
    """
    # 1. Load simulations
    raw_sim = _load_raw_cps_sim()
    enhanced_sim = _load_enhanced_cps_sim()

    # 2. Poverty rates
    raw_poverty = compute_child_poverty_rate(raw_sim, period=period)
    enhanced_poverty = compute_child_poverty_rate(enhanced_sim, period=period)

    # 3. Weight rebalancing
    weight_rebalancing = compute_weight_rebalancing(
        raw_sim, enhanced_sim, period=period
    )

    # 4. Tax gap
    raw_tax_gap = compute_tax_gap(raw_sim, period=period)
    enhanced_tax_gap = compute_tax_gap(enhanced_sim, period=period)

    # 5. State results
    state_results = compute_state_results(period=period)

    # 6. Build waterfall
    census = CENSUS_PUBLISHED_CHILD_POVERTY_2024
    waterfall = _build_waterfall(census, raw_poverty, enhanced_poverty)

    return {
        "census_benchmark": census,
        "raw_cps_poverty": raw_poverty,
        "enhanced_cps_poverty": enhanced_poverty,
        "weight_rebalancing": weight_rebalancing,
        "raw_cps_tax_gap": raw_tax_gap,
        "enhanced_cps_tax_gap": enhanced_tax_gap,
        "waterfall": waterfall,
        "state_results": state_results,
    }


def _build_waterfall(census, raw_poverty, enhanced_poverty) -> list[dict]:
    """Build the waterfall decomposition steps.

    The waterfall traces how child poverty diverges from the Census benchmark
    through successive analytical layers:

    1. Census published rate (internal file) -> 13.4%
    2. Privacy edits: Census internal -> public-use CPS reported
    3. PE modelling on raw CPS: reported -> PE-computed on raw CPS
    4. Weight recalibration: raw CPS reported -> enhanced CPS reported
    5. PE modelling on enhanced CPS: enhanced reported -> enhanced computed
    """
    raw_reported = raw_poverty["reported"]
    raw_computed = raw_poverty["computed"]
    enh_reported = enhanced_poverty["reported"]
    enh_computed = enhanced_poverty["computed"]

    waterfall = [
        {
            "label": "Census published rate (internal file)",
            "value": round(census, 4),
        },
        {
            "label": "Privacy edits (public-use CPS reported)",
            "value": round(raw_reported, 4),
            "delta": round(raw_reported - census, 4),
        },
        {
            "label": "PE tax/benefit modelling (raw CPS)",
            "value": round(raw_computed, 4),
            "delta": round(raw_computed - raw_reported, 4),
        },
        {
            "label": "Weight recalibration (enhanced CPS reported)",
            "value": round(enh_reported, 4),
            "delta": round(enh_reported - raw_reported, 4),
        },
        {
            "label": "PE tax/benefit modelling (enhanced CPS)",
            "value": round(enh_computed, 4),
            "delta": round(enh_computed - enh_reported, 4),
        },
    ]

    return waterfall
