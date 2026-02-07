"""How much does SSI explain of the TOTAL SPM poverty gap?

PE shows ~22.6% child poverty vs Census 13.4% - gap of ~9 ppts.
How much of that is the SSI take-up mismatch?
"""

import numpy as np
from policyengine_us import Microsimulation
from spm_decomposition.config import RAW_CPS_DATASET, ENHANCED_CPS_DATASET, YEAR

print("=" * 70)
print("TOTAL SPM POVERTY GAP DECOMPOSITION")
print("=" * 70)

# Load both datasets
print("\nLoading datasets...")
raw = Microsimulation(dataset=RAW_CPS_DATASET)
enhanced = Microsimulation(dataset=ENHANCED_CPS_DATASET)

period = YEAR

# ============================================================
# Setup for both datasets
# ============================================================
def analyze_dataset(sim, label):
    """Analyze SPM poverty for a dataset."""
    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"{'='*60}")

    # Person-level
    pw = sim.calc("person_weight", period=period).values
    is_child = sim.calc("is_child", period=period).values == 1
    child_pw = pw[is_child]
    total_children = float(child_pw.sum())

    # SPM unit mapping
    spm_unit_id = sim.calc("spm_unit_id", period=period).values
    person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
    spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}
    n_spm = len(spm_unit_id)

    def spm_to_person(spm_vals):
        return np.array([spm_vals[spm_id_to_idx[int(pid)]] for pid in person_spm_unit_id])

    def aggregate_person_to_spm(person_vals):
        spm_agg = np.zeros(n_spm)
        for i, pid in enumerate(person_spm_unit_id):
            idx = spm_id_to_idx[int(pid)]
            spm_agg[idx] += person_vals[i]
        return spm_agg

    # SPM threshold
    spm_threshold = sim.calc("spm_unit_spm_threshold", period=period).values
    spm_threshold_person = spm_to_person(spm_threshold)

    # Net income - PE computed
    spm_net_pe = sim.calc("spm_unit_net_income", period=period).values
    spm_net_pe_person = spm_to_person(spm_net_pe)

    # Net income - reported (if available)
    try:
        spm_net_reported = sim.calc("spm_unit_net_income_reported", period=period).values
        spm_net_reported_person = spm_to_person(spm_net_reported)
        has_reported = True
    except:
        has_reported = False

    # SSI values
    ssi_reported = sim.calc("ssi_reported", period=period).values
    ssi_pe = sim.calc("ssi", period=period).values
    ssi_reported_spm = aggregate_person_to_spm(ssi_reported)
    ssi_pe_spm = aggregate_person_to_spm(ssi_pe)

    # Adjusted net income: PE net income + (reported SSI - PE SSI)
    ssi_diff_spm = ssi_reported_spm - ssi_pe_spm
    ssi_diff_person = spm_to_person(ssi_diff_spm)
    spm_net_adjusted = spm_net_pe_person + ssi_diff_person

    # Poverty calculations
    is_poor_pe = spm_net_pe_person < spm_threshold_person
    is_poor_adjusted = spm_net_adjusted < spm_threshold_person

    poverty_pe = float(np.average(is_poor_pe[is_child], weights=child_pw))
    poverty_adjusted = float(np.average(is_poor_adjusted[is_child], weights=child_pw))

    print(f"\n  Total children: {total_children/1e6:.1f}M")
    print(f"\n  Child poverty (PE net income): {poverty_pe:.1%}")
    print(f"  Child poverty (PE + SSI fix): {poverty_adjusted:.1%}")
    print(f"  SSI fix contribution: {(poverty_pe - poverty_adjusted)*100:.2f} ppts")

    if has_reported:
        is_poor_reported = spm_net_reported_person < spm_threshold_person
        poverty_reported = float(np.average(is_poor_reported[is_child], weights=child_pw))
        print(f"  Child poverty (reported net income): {poverty_reported:.1%}")

    # How many children are in SSI households?
    in_ssi_hh = spm_to_person((ssi_reported_spm > 0).astype(float)) > 0
    children_in_ssi_hh = float((in_ssi_hh[is_child] * child_pw).sum())
    share_in_ssi_hh = children_in_ssi_hh / total_children
    print(f"\n  Children in SSI households: {children_in_ssi_hh/1e6:.2f}M ({share_in_ssi_hh:.1%})")

    return {
        'poverty_pe': poverty_pe,
        'poverty_adjusted': poverty_adjusted,
        'poverty_reported': poverty_reported if has_reported else None,
        'ssi_fix_ppts': (poverty_pe - poverty_adjusted) * 100,
        'share_in_ssi_hh': share_in_ssi_hh,
    }


# Run analysis
results_raw = analyze_dataset(raw, "RAW CPS")
results_enhanced = analyze_dataset(enhanced, "ENHANCED CPS")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY: HOW MUCH DOES SSI EXPLAIN?")
print("=" * 70)

census_rate = 0.134

print(f"""
Census published child poverty: {census_rate:.1%}

RAW CPS:
  PE-computed:     {results_raw['poverty_pe']:.1%}
  PE + SSI fix:    {results_raw['poverty_adjusted']:.1%}   (SSI fix = {results_raw['ssi_fix_ppts']:.2f} ppts)
  Reported income: {results_raw['poverty_reported']:.1%}

ENHANCED CPS:
  PE-computed:     {results_enhanced['poverty_pe']:.1%}
  PE + SSI fix:    {results_enhanced['poverty_adjusted']:.1%}   (SSI fix = {results_enhanced['ssi_fix_ppts']:.2f} ppts)
  Reported income: {results_enhanced['poverty_reported']:.1%}

Gap decomposition (Enhanced CPS):
  Total gap (PE vs Census):           {(results_enhanced['poverty_pe'] - census_rate)*100:+.1f} ppts
  SSI fix contribution:               {results_enhanced['ssi_fix_ppts']:.2f} ppts
  SSI as share of total gap:          {results_enhanced['ssi_fix_ppts'] / ((results_enhanced['poverty_pe'] - census_rate)*100) * 100:.0f}%

  Children in SSI HHs:                {results_enhanced['share_in_ssi_hh']:.1%} of all children

Remaining gap after SSI fix:          {(results_enhanced['poverty_adjusted'] - census_rate)*100:+.1f} ppts
""")

print("Done!")
