"""Decompose SSI household poverty rate discrepancy.

Investigates why PolicyEngine shows ~50% SSI household poverty while
Roosevelt Institute shows ~29% - despite both showing similar ~18 ppt
poverty reduction from SSI Restoration Act.

Key questions:
1. PE-computed SSI vs survey-reported SSI: amounts and recipients
2. Impact of Enhanced CPS weight recalibration on SSI households
3. Which component (benefits vs weights) drives the baseline gap?
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
import pandas as pd
from policyengine_us import Microsimulation
from spm_decomposition.config import ENHANCED_CPS_DATASET, RAW_CPS_DATASET, YEAR

print("=" * 70)
print("SSI HOUSEHOLD POVERTY DECOMPOSITION")
print("=" * 70)

# ============================================================
# Load simulations
# ============================================================
print("\nLoading datasets...")
enhanced = Microsimulation(dataset=ENHANCED_CPS_DATASET)
raw = Microsimulation(dataset=RAW_CPS_DATASET)

period = YEAR

# ============================================================
# Helper functions
# ============================================================
def get_spm_mapping(sim):
    """Get SPM unit ID mappings."""
    spm_unit_id = sim.calc("spm_unit_id", period=period).values
    person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
    spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}
    return spm_unit_id, person_spm_unit_id, spm_id_to_idx


def spm_to_person(spm_vals, person_spm_unit_id, spm_id_to_idx):
    """Map SPM-unit-level array to person-level array."""
    return np.array([spm_vals[spm_id_to_idx[int(pid)]] for pid in person_spm_unit_id])


def aggregate_person_to_spm(person_vals, person_spm_unit_id, spm_id_to_idx, n_spm):
    """Sum person-level values to SPM-unit level."""
    spm_agg = np.zeros(n_spm)
    for i, pid in enumerate(person_spm_unit_id):
        idx = spm_id_to_idx[int(pid)]
        spm_agg[idx] += person_vals[i]
    return spm_agg


# ============================================================
# ENHANCED CPS: SSI analysis
# ============================================================
print("\n" + "=" * 70)
print("ENHANCED CPS ANALYSIS")
print("=" * 70)

spm_id_e, person_spm_id_e, id_to_idx_e = get_spm_mapping(enhanced)
n_spm_e = len(spm_id_e)

# Person-level
pw_e = enhanced.calc("person_weight", period=period).values
spm_w_e = enhanced.calc("spm_unit_spm_threshold", period=period).weights

# SSI: PE-computed (person-level, aggregate to SPM)
ssi_person_e = enhanced.calc("ssi", period=period).values
ssi_spm_e = aggregate_person_to_spm(ssi_person_e, person_spm_id_e, id_to_idx_e, n_spm_e)

# SSI reported (if available)
try:
    ssi_reported_person_e = enhanced.calc("ssi_reported", period=period).values
    ssi_reported_spm_e = aggregate_person_to_spm(ssi_reported_person_e, person_spm_id_e, id_to_idx_e, n_spm_e)
    has_reported = True
except:
    print("  ssi_reported not available, trying alternative...")
    has_reported = False

# SPM poverty components
spm_threshold_e = enhanced.calc("spm_unit_spm_threshold", period=period).values
spm_net_income_e = enhanced.calc("spm_unit_net_income", period=period).values

# Try to get reported net income
try:
    spm_net_reported_e = enhanced.calc("spm_unit_net_income_reported", period=period).values
    has_reported_net = True
except:
    has_reported_net = False

# Identify SSI households (PE-computed)
ssi_hh_mask_e = ssi_spm_e > 0
n_ssi_hh_e = float((ssi_hh_mask_e * spm_w_e).sum())

# Poverty among SSI households
is_poor_e = spm_net_income_e < spm_threshold_e
ssi_hh_poverty_rate_e = float(np.average(is_poor_e[ssi_hh_mask_e], weights=spm_w_e[ssi_hh_mask_e]))

print(f"\n  PE-computed SSI households: {n_ssi_hh_e/1e6:.2f}M")
print(f"  PE-computed SSI total: ${float((ssi_spm_e * spm_w_e).sum())/1e9:.1f}B")
print(f"  Poverty rate among SSI HHs (PE net income): {ssi_hh_poverty_rate_e:.1%}")

if has_reported:
    ssi_reported_hh_mask_e = ssi_reported_spm_e > 0
    n_ssi_reported_hh_e = float((ssi_reported_hh_mask_e * spm_w_e).sum())
    print(f"\n  Reported SSI households: {n_ssi_reported_hh_e/1e6:.2f}M")
    print(f"  Reported SSI total: ${float((ssi_reported_spm_e * spm_w_e).sum())/1e9:.1f}B")

    # Poverty using reported SSI definition
    ssi_reported_poverty_e = float(np.average(is_poor_e[ssi_reported_hh_mask_e],
                                               weights=spm_w_e[ssi_reported_hh_mask_e]))
    print(f"  Poverty rate among reported SSI HHs: {ssi_reported_poverty_e:.1%}")

# ============================================================
# RAW CPS: SSI analysis (for weight comparison)
# ============================================================
print("\n" + "=" * 70)
print("RAW CPS ANALYSIS (weight comparison)")
print("=" * 70)

spm_id_r, person_spm_id_r, id_to_idx_r = get_spm_mapping(raw)
n_spm_r = len(spm_id_r)

pw_r = raw.calc("person_weight", period=period).values
spm_w_r = raw.calc("spm_unit_spm_threshold", period=period).weights

# SSI
ssi_person_r = raw.calc("ssi", period=period).values
ssi_spm_r = aggregate_person_to_spm(ssi_person_r, person_spm_id_r, id_to_idx_r, n_spm_r)

# SPM poverty
spm_threshold_r = raw.calc("spm_unit_spm_threshold", period=period).values
spm_net_income_r = raw.calc("spm_unit_net_income", period=period).values

try:
    spm_net_reported_r = raw.calc("spm_unit_net_income_reported", period=period).values
    has_reported_net_r = True
except:
    has_reported_net_r = False

# SSI households
ssi_hh_mask_r = ssi_spm_r > 0
n_ssi_hh_r = float((ssi_hh_mask_r * spm_w_r).sum())

is_poor_r = spm_net_income_r < spm_threshold_r
ssi_hh_poverty_rate_r = float(np.average(is_poor_r[ssi_hh_mask_r], weights=spm_w_r[ssi_hh_mask_r]))

print(f"\n  PE-computed SSI households: {n_ssi_hh_r/1e6:.2f}M")
print(f"  PE-computed SSI total: ${float((ssi_spm_r * spm_w_r).sum())/1e9:.1f}B")
print(f"  Poverty rate among SSI HHs (PE net income): {ssi_hh_poverty_rate_r:.1%}")

# Using reported net income if available
if has_reported_net_r:
    is_poor_reported_r = spm_net_reported_r < spm_threshold_r
    ssi_hh_poverty_reported_r = float(np.average(is_poor_reported_r[ssi_hh_mask_r],
                                                  weights=spm_w_r[ssi_hh_mask_r]))
    print(f"  Poverty rate among SSI HHs (reported net income): {ssi_hh_poverty_reported_r:.1%}")

# ============================================================
# DECOMPOSITION: Reported vs Computed vs Weights
# ============================================================
print("\n" + "=" * 70)
print("DECOMPOSITION: WHAT DRIVES THE GAP?")
print("=" * 70)

# Try to isolate the components
try:
    # Get reported SSI on raw CPS
    ssi_reported_person_r = raw.calc("ssi_reported", period=period).values
    ssi_reported_spm_r = aggregate_person_to_spm(ssi_reported_person_r, person_spm_id_r, id_to_idx_r, n_spm_r)

    ssi_reported_hh_mask_r = ssi_reported_spm_r > 0
    n_ssi_reported_hh_r = float((ssi_reported_hh_mask_r * spm_w_r).sum())

    print(f"\n  RAW CPS - Reported SSI households: {n_ssi_reported_hh_r/1e6:.2f}M")
    print(f"  RAW CPS - Reported SSI total: ${float((ssi_reported_spm_r * spm_w_r).sum())/1e9:.1f}B")

    if has_reported_net_r:
        # Poverty among reported SSI HHs using reported net income
        ssi_reported_poverty_reported_r = float(np.average(
            is_poor_reported_r[ssi_reported_hh_mask_r],
            weights=spm_w_r[ssi_reported_hh_mask_r]
        ))
        print(f"  Poverty (reported SSI HHs, reported net income): {ssi_reported_poverty_reported_r:.1%}")

        # Poverty among reported SSI HHs using PE net income
        ssi_reported_poverty_pe_r = float(np.average(
            is_poor_r[ssi_reported_hh_mask_r],
            weights=spm_w_r[ssi_reported_hh_mask_r]
        ))
        print(f"  Poverty (reported SSI HHs, PE net income): {ssi_reported_poverty_pe_r:.1%}")

except Exception as e:
    print(f"\n  Could not compute reported SSI decomposition: {e}")

# ============================================================
# COMPARE: Who gets SSI (reported vs computed)
# ============================================================
print("\n" + "=" * 70)
print("SSI RECIPIENT COMPARISON: REPORTED VS PE-COMPUTED")
print("=" * 70)

# On raw CPS
try:
    # Recipients
    ssi_recipients_reported_r = (ssi_reported_person_r > 0)
    ssi_recipients_pe_r = (ssi_person_r > 0)

    n_reported_recipients_r = float((ssi_recipients_reported_r * pw_r).sum())
    n_pe_recipients_r = float((ssi_recipients_pe_r * pw_r).sum())

    # Overlap
    both_r = ssi_recipients_reported_r & ssi_recipients_pe_r
    only_reported_r = ssi_recipients_reported_r & ~ssi_recipients_pe_r
    only_pe_r = ~ssi_recipients_reported_r & ssi_recipients_pe_r

    n_both_r = float((both_r * pw_r).sum())
    n_only_reported_r = float((only_reported_r * pw_r).sum())
    n_only_pe_r = float((only_pe_r * pw_r).sum())

    print(f"\n  RAW CPS (person-level):")
    print(f"    Reported SSI recipients: {n_reported_recipients_r/1e6:.2f}M")
    print(f"    PE-computed SSI recipients: {n_pe_recipients_r/1e6:.2f}M")
    print(f"    Both: {n_both_r/1e6:.2f}M")
    print(f"    Only reported (PE says ineligible): {n_only_reported_r/1e6:.2f}M")
    print(f"    Only PE (unreported/non-takeup): {n_only_pe_r/1e6:.2f}M")

    # Average benefits
    if n_both_r > 0:
        avg_reported_both = float(np.average(ssi_reported_person_r[both_r], weights=pw_r[both_r]))
        avg_pe_both = float(np.average(ssi_person_r[both_r], weights=pw_r[both_r]))
        print(f"\n    Among those in both:")
        print(f"      Avg reported SSI: ${avg_reported_both:,.0f}")
        print(f"      Avg PE-computed SSI: ${avg_pe_both:,.0f}")
        print(f"      Ratio (PE/reported): {avg_pe_both/avg_reported_both:.2f}")

except Exception as e:
    print(f"\n  Could not compare recipients: {e}")

# ============================================================
# INCOME DISTRIBUTION OF SSI HOUSEHOLDS
# ============================================================
print("\n" + "=" * 70)
print("INCOME DISTRIBUTION OF SSI HOUSEHOLDS")
print("=" * 70)

# Enhanced CPS
print(f"\n  ENHANCED CPS - SSI households by income relative to poverty:")
spm_income_ratio_e = spm_net_income_e / spm_threshold_e

for threshold, label in [(0.5, "Deep poverty (<50% SPM)"),
                          (1.0, "Poverty (<100% SPM)"),
                          (1.5, "Near-poor (<150% SPM)"),
                          (2.0, "<200% SPM")]:
    mask = ssi_hh_mask_e & (spm_income_ratio_e < threshold)
    share = float((mask * spm_w_e).sum()) / n_ssi_hh_e
    print(f"    {label}: {share:.1%}")

# Raw CPS
print(f"\n  RAW CPS - SSI households by income relative to poverty:")
spm_income_ratio_r = spm_net_income_r / spm_threshold_r

for threshold, label in [(0.5, "Deep poverty (<50% SPM)"),
                          (1.0, "Poverty (<100% SPM)"),
                          (1.5, "Near-poor (<150% SPM)"),
                          (2.0, "<200% SPM")]:
    mask = ssi_hh_mask_r & (spm_income_ratio_r < threshold)
    share = float((mask * spm_w_r).sum()) / n_ssi_hh_r
    print(f"    {label}: {share:.1%}")

# ============================================================
# WATERFALL: Isolate each factor
# ============================================================
print("\n" + "=" * 70)
print("WATERFALL: ISOLATING EACH FACTOR")
print("=" * 70)

print("""
Target: Roosevelt Institute baseline SSI HH poverty = 29.2%
PolicyEngine Enhanced CPS SSI HH poverty = {:.1%}
Gap to explain: {:.1f} percentage points
""".format(ssi_hh_poverty_rate_e, (ssi_hh_poverty_rate_e - 0.292) * 100))

print("Potential factors:")
print("  1. Who counts as SSI household (reported vs PE-computed eligibility)")
print("  2. Net income calculation (reported components vs PE-computed)")
print("  3. Weight recalibration (raw CPS vs enhanced CPS)")
print("  4. Data vintage (2024 CPS ASEC vs PolicyEngine 2026 projections)")

# Summary table
print("\n" + "=" * 70)
print("SUMMARY TABLE")
print("=" * 70)

print(f"\n{'Metric':<50} {'Raw CPS':>12} {'Enhanced':>12}")
print("-" * 74)
print(f"{'SSI households (PE-computed, millions)':<50} {n_ssi_hh_r/1e6:>12.2f} {n_ssi_hh_e/1e6:>12.2f}")
print(f"{'SSI spending (PE-computed, $B)':<50} {float((ssi_spm_r * spm_w_r).sum())/1e9:>12.1f} {float((ssi_spm_e * spm_w_e).sum())/1e9:>12.1f}")
print(f"{'Poverty rate among SSI HHs (PE net income)':<50} {ssi_hh_poverty_rate_r:>11.1%} {ssi_hh_poverty_rate_e:>11.1%}")

if has_reported_net_r:
    print(f"{'Poverty rate among SSI HHs (reported net income)':<50} {ssi_hh_poverty_reported_r:>11.1%} {'N/A':>12}")

print(f"\n{'Roosevelt Institute baseline':<50} {'29.2%':>12}")
print(f"{'Gap (PE Enhanced - Roosevelt)':<50} {(ssi_hh_poverty_rate_e - 0.292)*100:>+11.1f}pp")

print("\nDone!")
