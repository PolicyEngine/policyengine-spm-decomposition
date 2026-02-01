"""Extract comprehensive state-level data from HuggingFace state files.

Produces a single CSV/parquet with all key variables per state so we can
analyze without re-running simulations.

Uses local HuggingFace cache when available, falls back to hf:// URI.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
import pandas as pd
from policyengine_us import Microsimulation
from spm_decomposition.config import STATES, YEAR

# Local cache location for state .h5 files
CACHE_DIR = Path.home() / ".cache/huggingface/hub/models--policyengine--policyengine-us-data/snapshots"


def find_dataset_path(state: str) -> str:
    """Find dataset path: prefer local cache, fall back to hf:// URI."""
    # Check all snapshot directories for cached state files
    if CACHE_DIR.exists():
        for snapshot in CACHE_DIR.iterdir():
            local = snapshot / "states" / f"{state}.h5"
            if local.exists():
                return str(local)
    # Fall back to HuggingFace URI
    return f"hf://policyengine/policyengine-us-data/states/{state}.h5"


period = YEAR
rows = []

for i, state in enumerate(STATES):
    dataset_path = find_dataset_path(state)
    source = "cache" if not dataset_path.startswith("hf://") else "hf"
    print(f"[{i+1}/{len(STATES)}] {state} ({source})...", end=" ", flush=True)
    try:
        sim = Microsimulation(dataset=dataset_path)

        # Person-level basics
        is_child = sim.calc("is_child", period=period).values == 1
        pw = sim.calc("person_weight", period=period).values
        child_pw = pw[is_child]
        total_children = float(child_pw.sum())
        total_people = float(pw.sum())

        # SPM poverty (PE-computed)
        spm_threshold = sim.calc("spm_unit_spm_threshold", period=period, map_to="person").values
        spm_net_income = sim.calc("spm_unit_net_income", period=period, map_to="person").values
        is_poor = (spm_net_income < spm_threshold).astype(float)
        child_poverty = float(np.average(is_poor[is_child], weights=child_pw)) if total_children > 0 else 0
        total_poverty = float(np.average(is_poor, weights=pw)) if total_people > 0 else 0

        # Reported poverty
        spm_net_reported = sim.calc("spm_unit_net_income_reported", period=period, map_to="person").values
        is_poor_reported = (spm_net_reported < spm_threshold).astype(float)
        child_poverty_reported = float(np.average(is_poor_reported[is_child], weights=child_pw)) if total_children > 0 else 0

        # Program totals (SPM-unit level, weighted)
        spm_w = np.asarray(sim.calc("spm_unit_spm_threshold", period=period).weights)

        def spm_total(var):
            vals = sim.calc(var, period=period, map_to="spm_unit").values
            return float((vals * spm_w).sum())

        snap_total = spm_total("snap")
        ss_total = spm_total("social_security")
        ssi_total = spm_total("ssi")
        housing_total = spm_total("spm_unit_capped_housing_subsidy")
        school_meals_total = spm_total("free_school_meals") + spm_total("reduced_price_school_meals")
        eitc_total = spm_total("eitc")
        rctc_total = spm_total("refundable_ctc")
        tanf_total = spm_total("tanf")
        uc_total = spm_total("unemployment_compensation")
        wic_total = spm_total("wic")

        # Income/tax aggregates
        market_income = spm_total("spm_unit_market_income")
        benefits = spm_total("spm_unit_benefits")
        taxes = spm_total("spm_unit_taxes")
        fed_tax = spm_total("spm_unit_federal_tax")
        state_tax = spm_total("spm_unit_state_tax")
        net_income = spm_total("spm_unit_net_income")

        # Demographics
        try:
            cps_race = sim.calc("cps_race", period=period).values
            is_hispanic = sim.calc("is_hispanic", period=period).values
            pct_white = float(pw[is_child & (cps_race == 1)].sum() / total_children) if total_children > 0 else 0
            pct_black = float(pw[is_child & (cps_race == 2)].sum() / total_children) if total_children > 0 else 0
            pct_hispanic = float(pw[is_child & (is_hispanic == 1)].sum() / total_children) if total_children > 0 else 0
        except Exception:
            pct_white = pct_black = pct_hispanic = None

        row = {
            "state": state,
            "total_people": total_people,
            "total_children": total_children,
            "child_poverty_pe": child_poverty,
            "child_poverty_reported": child_poverty_reported,
            "total_poverty_pe": total_poverty,
            "snap_B": snap_total / 1e9,
            "social_security_B": ss_total / 1e9,
            "ssi_B": ssi_total / 1e9,
            "housing_B": housing_total / 1e9,
            "school_meals_B": school_meals_total / 1e9,
            "eitc_B": eitc_total / 1e9,
            "refundable_ctc_B": rctc_total / 1e9,
            "tanf_B": tanf_total / 1e9,
            "unemployment_comp_B": uc_total / 1e9,
            "wic_B": wic_total / 1e9,
            "market_income_B": market_income / 1e9,
            "total_benefits_B": benefits / 1e9,
            "total_taxes_B": taxes / 1e9,
            "federal_tax_B": fed_tax / 1e9,
            "state_tax_B": state_tax / 1e9,
            "net_income_B": net_income / 1e9,
            "pct_children_white": pct_white,
            "pct_children_black": pct_black,
            "pct_children_hispanic": pct_hispanic,
        }
        rows.append(row)
        print(f"child_pov={child_poverty:.1%}, children={total_children/1e6:.2f}M")
    except Exception as e:
        print(f"ERROR: {e}")
        rows.append({"state": state, "error": str(e)})

df = pd.DataFrame(rows)
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

# Save CSV and parquet
csv_path = output_dir / "state_data.csv"
parquet_path = output_dir / "state_data.parquet"
df.to_csv(csv_path, index=False)
df.to_parquet(parquet_path, index=False)

good = df[~df.columns.isin(["error"]) | df.get("error", pd.Series(dtype=str)).isna()]
n_good = len(df) - (df.get("error", pd.Series(dtype=str)).notna().sum() if "error" in df.columns else 0)
print(f"\nSaved {n_good}/{len(df)} states to {csv_path}")
print(df[["state", "child_poverty_pe", "child_poverty_reported", "total_children"]].to_string())
