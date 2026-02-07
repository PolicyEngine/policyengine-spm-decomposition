"""Full SPM poverty decomposition - all persons, all income components.

Investigate what drives the gap between PE poverty (~20%) and Census (~12%).
Break down by each income component: reported vs PE-computed.
"""

import numpy as np
import pandas as pd
from policyengine_us import Microsimulation
from spm_decomposition.config import RAW_CPS_DATASET, ENHANCED_CPS_DATASET, YEAR

print("=" * 80)
print("FULL SPM POVERTY DECOMPOSITION")
print("=" * 80)

# ============================================================
# Load datasets
# ============================================================
print("\nLoading datasets...")
raw = Microsimulation(dataset=RAW_CPS_DATASET)
enhanced = Microsimulation(dataset=ENHANCED_CPS_DATASET)

period = YEAR

def analyze_full_decomposition(sim, label):
    """Full decomposition of SPM poverty gap."""
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")

    # Person weights
    pw = sim.calc("person_weight", period=period).values
    total_pop = float(pw.sum())

    # Child flag
    is_child = sim.calc("is_child", period=period).values == 1
    child_pw = pw[is_child]
    adult_pw = pw[~is_child]

    # SPM unit mapping
    spm_unit_id = sim.calc("spm_unit_id", period=period).values
    person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
    spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}
    n_spm = len(spm_unit_id)
    spm_w = np.asarray(sim.calc("spm_unit_spm_threshold", period=period).weights)

    def spm_to_person(spm_vals):
        return np.array([spm_vals[spm_id_to_idx[int(pid)]] for pid in person_spm_unit_id])

    def aggregate_person_to_spm(person_vals):
        spm_agg = np.zeros(n_spm)
        for i, pid in enumerate(person_spm_unit_id):
            idx = spm_id_to_idx[int(pid)]
            spm_agg[idx] += person_vals[i]
        return spm_agg

    def sum_tax_units_to_spm(tu_var_name):
        tu_vals = sim.calc(tu_var_name, period=period).values
        tu_id = sim.calc("tax_unit_id", period=period).values
        person_tu_id = sim.calc("person_tax_unit_id", period=period).values
        tu_to_spm_idx = {}
        for i, ptid in enumerate(person_tu_id):
            tid = int(ptid)
            if tid not in tu_to_spm_idx:
                tu_to_spm_idx[tid] = spm_id_to_idx[int(person_spm_unit_id[i])]
        spm_agg = np.zeros(n_spm)
        for i, tid in enumerate(tu_id):
            spm_idx = tu_to_spm_idx.get(int(tid))
            if spm_idx is not None:
                spm_agg[spm_idx] += tu_vals[i]
        return spm_agg

    # SPM threshold
    spm_threshold = sim.calc("spm_unit_spm_threshold", period=period).values
    spm_threshold_person = spm_to_person(spm_threshold)

    # Net income - PE computed and reported
    spm_net_pe = sim.calc("spm_unit_net_income", period=period).values
    spm_net_pe_person = spm_to_person(spm_net_pe)

    try:
        spm_net_reported = sim.calc("spm_unit_net_income_reported", period=period).values
        spm_net_reported_person = spm_to_person(spm_net_reported)
        has_reported = True
    except:
        has_reported = False

    # ============================================================
    # Baseline poverty rates
    # ============================================================
    is_poor_pe = spm_net_pe_person < spm_threshold_person
    poverty_pe_all = float(np.average(is_poor_pe, weights=pw))
    poverty_pe_child = float(np.average(is_poor_pe[is_child], weights=child_pw))
    poverty_pe_adult = float(np.average(is_poor_pe[~is_child], weights=adult_pw))

    print(f"\n--- POVERTY RATES (PE net income) ---")
    print(f"  All persons: {poverty_pe_all:.1%}")
    print(f"  Children:    {poverty_pe_child:.1%}")
    print(f"  Adults:      {poverty_pe_adult:.1%}")

    if has_reported:
        is_poor_reported = spm_net_reported_person < spm_threshold_person
        poverty_reported_all = float(np.average(is_poor_reported, weights=pw))
        poverty_reported_child = float(np.average(is_poor_reported[is_child], weights=child_pw))
        poverty_reported_adult = float(np.average(is_poor_reported[~is_child], weights=adult_pw))

        print(f"\n--- POVERTY RATES (reported net income) ---")
        print(f"  All persons: {poverty_reported_all:.1%}")
        print(f"  Children:    {poverty_reported_child:.1%}")
        print(f"  Adults:      {poverty_reported_adult:.1%}")

        print(f"\n--- GAP (PE - reported) ---")
        print(f"  All persons: {(poverty_pe_all - poverty_reported_all)*100:+.1f} ppts")
        print(f"  Children:    {(poverty_pe_child - poverty_reported_child)*100:+.1f} ppts")
        print(f"  Adults:      {(poverty_pe_adult - poverty_reported_adult)*100:+.1f} ppts")

    # ============================================================
    # Income component comparison
    # ============================================================
    print(f"\n--- INCOME COMPONENTS (mean per SPM unit) ---")
    print(f"{'Component':<45} {'PE':>12} {'Reported':>12} {'Gap':>12}")
    print("-" * 81)

    # Get reported vs PE for key components
    components = []

    # Benefits with reported equivalents
    benefit_pairs = [
        ("ssi", "ssi_reported", "SSI", "person"),
        ("snap", "snap_reported", "SNAP", "spm"),
        ("tanf", "tanf_reported", "TANF", "spm"),
        ("social_security", "social_security_reported", "Social Security", "person"),
    ]

    for pe_var, reported_var, label, level in benefit_pairs:
        try:
            if level == "person":
                pe_vals = aggregate_person_to_spm(sim.calc(pe_var, period=period).values)
                reported_vals = aggregate_person_to_spm(sim.calc(reported_var, period=period).values)
            else:
                pe_vals = sim.calc(pe_var, period=period).values
                reported_vals = sim.calc(reported_var, period=period).values

            mean_pe = float(np.average(pe_vals, weights=spm_w))
            mean_reported = float(np.average(reported_vals, weights=spm_w))
            gap = mean_pe - mean_reported

            print(f"{label:<45} ${mean_pe:>10,.0f} ${mean_reported:>10,.0f} ${gap:>+10,.0f}")
            components.append({
                'name': label,
                'pe': mean_pe,
                'reported': mean_reported,
                'gap': gap,
                'pe_spm': pe_vals,
                'reported_spm': reported_vals,
            })
        except Exception as e:
            print(f"{label:<45} ERROR: {e}")

    # Tax credits (PE only, no reported equivalent usually)
    print(f"\n--- TAX CREDITS (PE-computed, adds to income) ---")
    credit_vars = [
        ("eitc", "EITC"),
        ("ctc", "CTC (total)"),
        ("refundable_ctc", "CTC (refundable)"),
    ]

    for var, label in credit_vars:
        try:
            vals = sum_tax_units_to_spm(var)
            mean_val = float(np.average(vals, weights=spm_w))
            print(f"  {label:<43} ${mean_val:>10,.0f}")
        except Exception as e:
            print(f"  {label:<43} ERROR: {e}")

    # Taxes
    print(f"\n--- TAXES (PE-computed, subtracts from income) ---")
    tax_vars = [
        ("spm_unit_federal_tax", "Federal tax (net of credits)"),
        ("spm_unit_payroll_tax", "Payroll tax"),
        ("spm_unit_state_tax", "State/local tax"),
    ]

    for var, label in tax_vars:
        try:
            vals = sim.calc(var, period=period).values
            mean_val = float(np.average(vals, weights=spm_w))
            print(f"  {label:<43} ${mean_val:>10,.0f}")
        except Exception as e:
            print(f"  {label:<43} ERROR: {e}")

    # ============================================================
    # Component-by-component poverty impact
    # ============================================================
    print(f"\n--- POVERTY IMPACT OF EACH COMPONENT GAP ---")
    print(f"(What happens to poverty if we replace PE value with reported value)")
    print(f"{'Component':<30} {'Poverty Δ (all)':>15} {'Poverty Δ (child)':>18}")
    print("-" * 63)

    for comp in components:
        # Adjusted net income: PE net income - PE component + reported component
        # = PE net income + (reported - PE) for this component
        diff_spm = comp['reported_spm'] - comp['pe_spm']
        diff_person = spm_to_person(diff_spm)
        adjusted_net = spm_net_pe_person + diff_person

        is_poor_adj = adjusted_net < spm_threshold_person
        poverty_adj_all = float(np.average(is_poor_adj, weights=pw))
        poverty_adj_child = float(np.average(is_poor_adj[is_child], weights=child_pw))

        delta_all = (poverty_adj_all - poverty_pe_all) * 100
        delta_child = (poverty_adj_child - poverty_pe_child) * 100

        print(f"{comp['name']:<30} {delta_all:>+14.2f}pp {delta_child:>+17.2f}pp")

    # ============================================================
    # Cumulative fix
    # ============================================================
    if has_reported:
        print(f"\n--- CUMULATIVE EFFECT ---")
        print(f"{'Scenario':<50} {'All':>10} {'Child':>10}")
        print("-" * 70)
        print(f"{'PE net income':<50} {poverty_pe_all:>9.1%} {poverty_pe_child:>9.1%}")

        # Add all component fixes
        total_diff_spm = np.zeros(n_spm)
        for comp in components:
            total_diff_spm += comp['reported_spm'] - comp['pe_spm']

        total_diff_person = spm_to_person(total_diff_spm)
        adjusted_net_all = spm_net_pe_person + total_diff_person

        is_poor_adj_all = adjusted_net_all < spm_threshold_person
        poverty_adj_all_all = float(np.average(is_poor_adj_all, weights=pw))
        poverty_adj_all_child = float(np.average(is_poor_adj_all[is_child], weights=child_pw))

        print(f"{'PE + all reported benefit fixes':<50} {poverty_adj_all_all:>9.1%} {poverty_adj_all_child:>9.1%}")
        print(f"{'Reported net income':<50} {poverty_reported_all:>9.1%} {poverty_reported_child:>9.1%}")

        print(f"\n  Gap explained by benefit fixes: {(poverty_pe_all - poverty_adj_all_all)*100:.1f}pp of {(poverty_pe_all - poverty_reported_all)*100:.1f}pp")
        print(f"  Remaining gap: {(poverty_adj_all_all - poverty_reported_all)*100:.1f}pp")

    return {
        'poverty_pe_all': poverty_pe_all,
        'poverty_pe_child': poverty_pe_child,
        'poverty_reported_all': poverty_reported_all if has_reported else None,
        'poverty_reported_child': poverty_reported_child if has_reported else None,
    }


# Run analysis on both datasets
results_raw = analyze_full_decomposition(raw, "RAW CPS (original weights)")
results_enhanced = analyze_full_decomposition(enhanced, "ENHANCED CPS (recalibrated weights)")

# ============================================================
# Cross-dataset comparison
# ============================================================
print(f"\n{'='*80}")
print("SUMMARY: RAW vs ENHANCED CPS")
print(f"{'='*80}")

census_all = 0.116  # Approximate Census SPM all-person rate
census_child = 0.134

print(f"\n{'Metric':<40} {'Census':>10} {'Raw CPS':>12} {'Enhanced':>12}")
print("-" * 74)
print(f"{'All-person poverty (PE)':<40} {census_all:>9.1%} {results_raw['poverty_pe_all']:>11.1%} {results_enhanced['poverty_pe_all']:>11.1%}")
print(f"{'All-person poverty (reported)':<40} {'-':>10} {results_raw['poverty_reported_all']:>11.1%} {results_enhanced['poverty_reported_all']:>11.1%}")
print(f"{'Child poverty (PE)':<40} {census_child:>9.1%} {results_raw['poverty_pe_child']:>11.1%} {results_enhanced['poverty_pe_child']:>11.1%}")
print(f"{'Child poverty (reported)':<40} {'-':>10} {results_raw['poverty_reported_child']:>11.1%} {results_enhanced['poverty_reported_child']:>11.1%}")

print(f"\n--- KEY INSIGHT ---")
print(f"""
The gap between PE and Census poverty comes from multiple sources:

1. BENEFIT COMPUTATION: PE computes benefits from rules; CPS uses reported amounts
   - SSI, SNAP, Social Security, TANF all differ
   - These differences shift household income distributions

2. TAX COMPUTATION: PE computes taxes from rules; CPS uses reported amounts
   - Federal tax (including EITC/CTC) differs
   - This affects net income

3. WEIGHT RECALIBRATION: Enhanced CPS reweights to IRS/SOI targets
   - This shifts the population toward different income groups
   - Raw CPS → Enhanced CPS changes poverty even with same income calc

4. DATA VINTAGE: PE projects to 2026; Census publishes 2024 data
""")

print("\nDone!")
