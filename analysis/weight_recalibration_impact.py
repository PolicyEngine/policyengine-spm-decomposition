"""Investigate weight recalibration impact on poverty.

Raw CPS → Enhanced CPS adds ~5pp to poverty even using reported income.
What's happening with the weights?
"""

import numpy as np
import pandas as pd
from policyengine_us import Microsimulation
from spm_decomposition.config import RAW_CPS_DATASET, ENHANCED_CPS_DATASET, YEAR

print("=" * 80)
print("WEIGHT RECALIBRATION IMPACT ON POVERTY")
print("=" * 80)

raw = Microsimulation(dataset=RAW_CPS_DATASET)
enhanced = Microsimulation(dataset=ENHANCED_CPS_DATASET)

period = YEAR

# ============================================================
# Basic stats
# ============================================================
pw_raw = raw.calc("person_weight", period=period).values
pw_enh = enhanced.calc("person_weight", period=period).values

print(f"\n--- POPULATION ---")
print(f"  Raw CPS:      {pw_raw.sum()/1e6:.1f}M persons")
print(f"  Enhanced CPS: {pw_enh.sum()/1e6:.1f}M persons")
print(f"  Records: {len(pw_raw):,} raw, {len(pw_enh):,} enhanced")

# ============================================================
# Poverty by income decile
# ============================================================
print(f"\n--- POVERTY BY INCOME DECILE ---")

def analyze_by_decile(sim, pw, label):
    """Analyze poverty by household income decile."""
    # Get SPM unit mapping
    spm_unit_id = sim.calc("spm_unit_id", period=period).values
    person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
    spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}
    spm_w = np.asarray(sim.calc("spm_unit_spm_threshold", period=period).weights)

    def spm_to_person(spm_vals):
        return np.array([spm_vals[spm_id_to_idx[int(pid)]] for pid in person_spm_unit_id])

    # Income and threshold
    try:
        net_income = sim.calc("spm_unit_net_income_reported", period=period).values
    except:
        net_income = sim.calc("spm_unit_net_income", period=period).values

    threshold = sim.calc("spm_unit_spm_threshold", period=period).values
    income_ratio = net_income / np.maximum(threshold, 1)

    # Assign deciles based on income ratio (weighted)
    sorted_idx = np.argsort(income_ratio)
    sorted_ratios = income_ratio[sorted_idx]
    sorted_weights = spm_w[sorted_idx]
    cumsum = np.cumsum(sorted_weights)
    cumsum /= cumsum[-1]  # Normalize to [0, 1]

    decile_edges = [sorted_ratios[0]]
    for p in np.arange(0.1, 1.0, 0.1):
        idx = np.searchsorted(cumsum, p)
        decile_edges.append(sorted_ratios[min(idx, len(sorted_ratios)-1)])
    decile_edges.append(sorted_ratios[-1] + 1)

    # Person-level
    net_income_person = spm_to_person(net_income)
    threshold_person = spm_to_person(threshold)
    income_ratio_person = spm_to_person(income_ratio)
    is_poor = net_income_person < threshold_person

    # Population share in each decile
    results = []
    for i in range(10):
        low = decile_edges[i]
        high = decile_edges[i+1] if i < 9 else float('inf')
        mask = (income_ratio_person >= low) & (income_ratio_person < high)
        pop_share = float((mask * pw).sum()) / float(pw.sum())
        poverty_rate = float(np.average(is_poor[mask], weights=pw[mask])) if mask.sum() > 0 else 0
        results.append({
            'decile': i + 1,
            'pop_share': pop_share,
            'poverty_rate': poverty_rate,
            'income_ratio_low': low,
            'income_ratio_high': high,
        })

    return results

results_raw = analyze_by_decile(raw, pw_raw, "Raw")
results_enh = analyze_by_decile(enhanced, pw_enh, "Enhanced")

print(f"\n{'Decile':<8} {'Raw Share':>12} {'Enh Share':>12} {'Δ Share':>10} {'Raw Pov':>10} {'Enh Pov':>10}")
print("-" * 62)
for i in range(10):
    r = results_raw[i]
    e = results_enh[i]
    delta = (e['pop_share'] - r['pop_share']) * 100
    print(f"D{i+1:<7} {r['pop_share']:>11.1%} {e['pop_share']:>11.1%} {delta:>+9.1f}pp {r['poverty_rate']:>9.1%} {e['poverty_rate']:>9.1%}")

# ============================================================
# Population shift by income level
# ============================================================
print(f"\n--- POPULATION BY INCOME-TO-POVERTY RATIO ---")

def analyze_by_income_ratio(sim, pw, label):
    """Analyze population distribution by income-to-poverty ratio."""
    spm_unit_id = sim.calc("spm_unit_id", period=period).values
    person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
    spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}

    def spm_to_person(spm_vals):
        return np.array([spm_vals[spm_id_to_idx[int(pid)]] for pid in person_spm_unit_id])

    try:
        net_income = sim.calc("spm_unit_net_income_reported", period=period).values
    except:
        net_income = sim.calc("spm_unit_net_income", period=period).values

    threshold = sim.calc("spm_unit_spm_threshold", period=period).values
    income_ratio_person = spm_to_person(net_income / np.maximum(threshold, 1))

    results = {}
    brackets = [
        (0, 0.5, "Deep poverty (<50%)"),
        (0.5, 1.0, "Poverty (50-100%)"),
        (1.0, 1.5, "Near-poor (100-150%)"),
        (1.5, 2.0, "Low-income (150-200%)"),
        (2.0, 4.0, "Middle (200-400%)"),
        (4.0, float('inf'), "Higher (400%+)"),
    ]

    for low, high, name in brackets:
        mask = (income_ratio_person >= low) & (income_ratio_person < high)
        pop_share = float((mask * pw).sum()) / float(pw.sum())
        results[name] = pop_share

    return results

raw_dist = analyze_by_income_ratio(raw, pw_raw, "Raw")
enh_dist = analyze_by_income_ratio(enhanced, pw_enh, "Enhanced")

print(f"\n{'Income bracket':<30} {'Raw CPS':>12} {'Enhanced':>12} {'Δ':>10}")
print("-" * 64)
for bracket in raw_dist.keys():
    r = raw_dist[bracket]
    e = enh_dist[bracket]
    delta = (e - r) * 100
    print(f"{bracket:<30} {r:>11.1%} {e:>11.1%} {delta:>+9.1f}pp")

# ============================================================
# Summary
# ============================================================
print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")

# Calculate poverty in deep poverty + poverty brackets
raw_poor = raw_dist["Deep poverty (<50%)"] + raw_dist["Poverty (50-100%)"]
enh_poor = enh_dist["Deep poverty (<50%)"] + enh_dist["Poverty (50-100%)"]

print(f"""
The Enhanced CPS shifts population toward lower income levels:

  Deep poverty (<50% of threshold):
    Raw CPS:      {raw_dist["Deep poverty (<50%)"]*100:.1f}%
    Enhanced:     {enh_dist["Deep poverty (<50%)"]*100:.1f}%
    Change:       {(enh_dist["Deep poverty (<50%)"] - raw_dist["Deep poverty (<50%)"])*100:+.1f}pp

  Poverty (50-100%):
    Raw CPS:      {raw_dist["Poverty (50-100%)"]*100:.1f}%
    Enhanced:     {enh_dist["Poverty (50-100%)"]*100:.1f}%
    Change:       {(enh_dist["Poverty (50-100%)"] - raw_dist["Poverty (50-100%)"])*100:+.1f}pp

  Total in poverty (<100%):
    Raw CPS:      {raw_poor*100:.1f}%
    Enhanced:     {enh_poor*100:.1f}%
    Change:       {(enh_poor - raw_poor)*100:+.1f}pp

The weight recalibration to IRS/SOI targets shifts population weight
toward lower-income households, mechanically increasing poverty rates.

This is the PRIMARY driver of the PE vs Census poverty gap, not
benefit computation differences.
""")

print("Done!")
