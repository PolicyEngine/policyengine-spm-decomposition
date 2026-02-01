"""Run the full decomposition pipeline and produce JSON matching the app schema.

Usage:
    uv run python run_pipeline.py [--skip-states]
"""

import json
import sys
import time
from pathlib import Path

from policyengine_us import Microsimulation

from spm_decomposition.config import (
    CENSUS_PUBLISHED_CHILD_POVERTY_2024,
    ENHANCED_CPS_DATASET,
    RAW_CPS_DATASET,
    YEAR,
)
from spm_decomposition.poverty import compute_child_poverty_rate
from spm_decomposition.weights import compute_weight_rebalancing
from spm_decomposition.tax_gap import compute_tax_gap
from spm_decomposition.states import compute_state_results


def main():
    skip_states = "--skip-states" in sys.argv
    start = time.time()

    # ── Load simulations ──────────────────────────────────────────────
    print(f"Loading raw CPS from {RAW_CPS_DATASET}...")
    t0 = time.time()
    raw_sim = Microsimulation(dataset=RAW_CPS_DATASET)
    print(f"  Raw CPS loaded in {time.time() - t0:.1f}s")

    print(f"Loading enhanced CPS from {ENHANCED_CPS_DATASET}...")
    t0 = time.time()
    enhanced_sim = Microsimulation(dataset=ENHANCED_CPS_DATASET)
    print(f"  Enhanced CPS loaded in {time.time() - t0:.1f}s")

    # ── Poverty rates ─────────────────────────────────────────────────
    print("Computing child poverty rates...")
    raw_poverty = compute_child_poverty_rate(raw_sim, period=YEAR)
    enhanced_poverty = compute_child_poverty_rate(enhanced_sim, period=YEAR)
    print(f"  Raw CPS:      computed={raw_poverty['computed']:.4f}  reported={raw_poverty['reported']:.4f}")
    print(f"  Enhanced CPS: computed={enhanced_poverty['computed']:.4f}  reported={enhanced_poverty['reported']:.4f}")

    # ── Weight rebalancing ────────────────────────────────────────────
    print("Computing weight rebalancing...")
    weight_rebalancing = compute_weight_rebalancing(raw_sim, enhanced_sim, period=YEAR)
    print(f"  {len(weight_rebalancing['groups'])} groups")

    # ── Tax gap ───────────────────────────────────────────────────────
    print("Computing tax gap (enhanced CPS)...")
    tax_gap = compute_tax_gap(enhanced_sim, period=YEAR)
    d10 = tax_gap[-1]
    print(f"  D10 gap: ${d10['gap']:,.0f}")

    # ── State results ─────────────────────────────────────────────────
    if skip_states:
        print("Skipping state-level analysis (--skip-states)")
        state_results = []
    else:
        print("Computing state-level results (this takes ~13 min)...")
        t0 = time.time()
        state_results = compute_state_results(period=YEAR)
        print(f"  {len(state_results)} states in {time.time() - t0:.1f}s")

    total_time = time.time() - start

    # ── Build app JSON ────────────────────────────────────────────────
    census = CENSUS_PUBLISHED_CHILD_POVERTY_2024

    # Waterfall steps (matching app schema)
    steps = [
        {"label": "Census published (2024)", "value": round(census, 4)},
        {"label": "Raw CPS reported (2024)", "value": round(raw_poverty["reported"], 4)},
        {"label": "Raw CPS PE-computed (2024)", "value": round(raw_poverty["computed"], 4)},
        {"label": "Enhanced CPS reported (2024)", "value": round(enhanced_poverty["reported"], 4)},
        {"label": "Enhanced CPS PE-computed (2024)", "value": round(enhanced_poverty["computed"], 4)},
    ]

    deltas = [
        {
            "from": steps[0]["label"],
            "to": steps[1]["label"],
            "delta": round(steps[1]["value"] - steps[0]["value"], 4),
            "explanation": "Public-use ASEC vs internal Census file (privacy edits, minor corrections)",
        },
        {
            "from": steps[1]["label"],
            "to": steps[2]["label"],
            "delta": round(steps[2]["value"] - steps[1]["value"], 4),
            "explanation": "PE tax/benefit modeling on raw CPS data",
        },
        {
            "from": steps[2]["label"],
            "to": steps[3]["label"],
            "delta": round(steps[3]["value"] - steps[2]["value"], 4),
            "explanation": "Enhanced CPS weight recalibration to IRS SOI targets + PUF income imputation",
        },
        {
            "from": steps[3]["label"],
            "to": steps[4]["label"],
            "delta": round(steps[4]["value"] - steps[3]["value"], 4),
            "explanation": "PE tax/benefit modeling on enhanced CPS (PUF-imputed income taxed higher)",
        },
    ]

    from importlib.metadata import version as pkg_version

    output = {
        "waterfall": {"steps": steps, "deltas": deltas},
        "weight_rebalancing": weight_rebalancing,
        "tax_gap_by_decile": [
            {k: round(v, 2) if isinstance(v, float) else v for k, v in d.items()}
            for d in tax_gap
        ],
        "state_results": [
            {
                "state": s["state"],
                "reported_child_poverty": round(s["reported_child_poverty"], 4),
                "computed_child_poverty": round(s["computed_child_poverty"], 4),
                "total_children": round(s["total_children"]),
            }
            for s in state_results
        ],
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "policyengine_us_version": pkg_version("policyengine-us"),
            "raw_cps_dataset": RAW_CPS_DATASET,
            "enhanced_cps_dataset": ENHANCED_CPS_DATASET,
            "total_runtime_seconds": round(total_time, 1),
        },
    }

    # Write output
    output_path = Path(__file__).parent / "output" / "decomposition.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nOutput written to {output_path}")
    print(f"Total runtime: {total_time:.1f}s")

    # Also copy to app public dir
    app_path = Path(__file__).parent.parent / "app" / "public" / "decomposition.json"
    with open(app_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Also copied to {app_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    main()
