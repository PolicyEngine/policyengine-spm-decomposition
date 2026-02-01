"""Decompose SPM child poverty by program and demographics.

Compares PolicyEngine's enhanced CPS against Census published benchmarks.

Key architecture from policyengine-us:
  spm_unit_net_income = spm_unit_market_income + spm_unit_benefits
                        - spm_unit_taxes - spm_unit_spm_expenses

  spm_unit_benefits includes: snap, social_security, ssi, free_school_meals,
    reduced_price_school_meals, wic, tanf, spm_unit_capped_housing_subsidy,
    spm_unit_energy_subsidy, unemployment_compensation, etc.

  spm_unit_taxes includes: spm_unit_federal_tax (= sum of income_tax across
    contained tax units — income_tax includes EITC/CTC as credits),
    spm_unit_payroll_tax, spm_unit_state_tax, etc.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
from policyengine_us import Microsimulation
from spm_decomposition.config import ENHANCED_CPS_DATASET, RAW_CPS_DATASET, YEAR

# ============================================================
# Load simulations
# ============================================================
print("Loading enhanced CPS...")
sim = Microsimulation(dataset=ENHANCED_CPS_DATASET)
print("Loading raw CPS...")
raw_sim = Microsimulation(dataset=RAW_CPS_DATASET)

period = YEAR

# ============================================================
# Helper: map SPM-unit-level values to person level
# ============================================================
spm_unit_id = sim.calc("spm_unit_id", period=period).values
person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}
spm_w = np.asarray(sim.calc("spm_unit_spm_threshold", period=period).weights)


def spm_to_person(spm_vals):
    """Map SPM-unit-level array to person-level array."""
    return np.array([spm_vals[spm_id_to_idx[int(pid)]] for pid in person_spm_unit_id])


def aggregate_person_to_spm(person_vals):
    """Sum person-level values to SPM-unit level."""
    spm_agg = np.zeros(len(spm_unit_id))
    for i, pid in enumerate(person_spm_unit_id):
        idx = spm_id_to_idx[int(pid)]
        spm_agg[idx] += person_vals[i]
    return spm_agg


def sum_tax_units_to_spm(tu_var_name):
    """Sum a tax-unit variable to SPM-unit level (return SPM-unit array).

    Maps each TU directly to its containing SPM unit to avoid double-counting
    that occurs when mapping TU values to all persons then aggregating.
    """
    tu_vals = sim.calc(tu_var_name, period=period).values
    tu_id = sim.calc("tax_unit_id", period=period).values
    person_tu_id = sim.calc("person_tax_unit_id", period=period).values

    # Build TU → SPM mapping (first person encountered determines it)
    tu_to_spm_idx = {}
    for i, ptid in enumerate(person_tu_id):
        tid = int(ptid)
        if tid not in tu_to_spm_idx:
            tu_to_spm_idx[tid] = spm_id_to_idx[int(person_spm_unit_id[i])]

    spm_agg = np.zeros(len(spm_unit_id))
    for i, tid in enumerate(tu_id):
        spm_idx = tu_to_spm_idx.get(int(tid))
        if spm_idx is not None:
            spm_agg[spm_idx] += tu_vals[i]
    return spm_agg


def weighted_total_spm(spm_vals):
    """Weighted total using SPM-unit weights."""
    return float((spm_vals * spm_w).sum())


# Person-level variables
is_child = sim.calc("is_child", period=period).values == 1
pw = sim.calc("person_weight", period=period).values
age = sim.calc("age", period=period).values
child_pw = pw[is_child]
total_children = float(child_pw.sum())

# SPM poverty: person is poor if SPM unit's net_income < threshold
spm_threshold_spm = sim.calc("spm_unit_spm_threshold", period=period).values
spm_net_income_spm = sim.calc("spm_unit_net_income", period=period).values
spm_threshold_person = spm_to_person(spm_threshold_spm)
spm_net_income_person = spm_to_person(spm_net_income_spm)
is_poor = (spm_net_income_person < spm_threshold_person).astype(float)

overall_rate = float(np.average(is_poor[is_child], weights=child_pw))
children_in_poverty = float((is_poor[is_child] * child_pw).sum())

print(f"\n{'='*70}")
print(f"ENHANCED CPS: SPM CHILD POVERTY RATE")
print(f"{'='*70}")
print(f"  PE-computed:      {overall_rate:.1%} ({children_in_poverty/1e6:.2f}M of {total_children/1e6:.1f}M)")
print(f"  Census published: 13.4%")

# ============================================================
# PROGRAM EFFECTS: Remove each program, recalculate poverty
# ============================================================
print(f"\n{'='*70}")
print(f"PROGRAM EFFECTS ON CHILD SPM POVERTY (Enhanced CPS)")
print(f"Methodology: subtract program from SPM net income, recalc poverty")
print(f"{'='*70}")


def compute_program_effect(benefit_spm_level, label, annualize=1):
    """Compute poverty effect of removing a benefit.

    benefit_spm_level: SPM-unit-level benefit amounts.
    annualize: multiply by this to annualize (e.g., 12 for monthly vars).
    """
    benefit_annual = benefit_spm_level * annualize
    benefit_person = spm_to_person(benefit_annual)

    # Net income without this benefit
    net_without = spm_net_income_person - benefit_person
    poor_without = (net_without < spm_threshold_person).astype(float)

    rate_with = float(np.average(is_poor[is_child], weights=child_pw))
    rate_without = float(np.average(poor_without[is_child], weights=child_pw))

    children_lifted = float(((poor_without - is_poor) * pw)[is_child].sum())
    total_lifted = float(((poor_without - is_poor) * pw).sum())

    # Weighted total using SPM unit weights (correct accounting)
    total_benefit = weighted_total_spm(benefit_annual)

    return {
        "label": label,
        "rate_with": rate_with,
        "rate_without": rate_without,
        "children_lifted": children_lifted,
        "total_lifted": total_lifted,
        "total_benefit_B": total_benefit / 1e9,
    }


# --- SNAP ---
# NOTE: snap has definition_period=MONTH, but sim.calc("snap", period=2024)
# returns annualized values (sum of 12 months). No need to multiply by 12.
print("\n  SNAP (PE-computed):")
snap_spm = sim.calc("snap", period=period).values  # already annualized by PE
r_snap = compute_program_effect(snap_spm, "SNAP")
print(f"    Total: ${r_snap['total_benefit_B']:.1f}B (actual: ~$113B)")
print(f"    Children lifted: {r_snap['children_lifted']/1e6:.2f}M (Census: 1.4M)")
print(f"    Poverty: {r_snap['rate_without']:.1%} → {r_snap['rate_with']:.1%}")

# --- Social Security ---
print("\n  Social Security:")
ss_person_raw = sim.calc("social_security", period=period).values
ss_spm = aggregate_person_to_spm(ss_person_raw)
r_ss = compute_program_effect(ss_spm, "Social Security")
print(f"    Total: ${r_ss['total_benefit_B']:.1f}B (actual: ~$1.3T)")
print(f"    Children lifted: {r_ss['children_lifted']/1e6:.2f}M")
print(f"    Total people lifted: {r_ss['total_lifted']/1e6:.2f}M (Census: 28.7M)")
print(f"    Poverty: {r_ss['rate_without']:.1%} → {r_ss['rate_with']:.1%}")

# --- SSI ---
print("\n  SSI:")
ssi_person_raw = sim.calc("ssi", period=period).values
ssi_spm = aggregate_person_to_spm(ssi_person_raw)
r_ssi = compute_program_effect(ssi_spm, "SSI")
print(f"    Total: ${r_ssi['total_benefit_B']:.1f}B (actual: ~$56B)")
print(f"    Children lifted: {r_ssi['children_lifted']/1e6:.2f}M (Census: ~0.5M)")
print(f"    Poverty: {r_ssi['rate_without']:.1%} → {r_ssi['rate_with']:.1%}")

# --- Housing subsidies (reported) ---
print("\n  Housing subsidies (reported):")
housing_spm = sim.calc("spm_unit_capped_housing_subsidy", period=period).values
r_housing = compute_program_effect(housing_spm, "Housing subsidies")
print(f"    Total: ${r_housing['total_benefit_B']:.1f}B (actual: ~$50B)")
print(f"    Children lifted: {r_housing['children_lifted']/1e6:.2f}M")
print(f"    Total people lifted: {r_housing['total_lifted']/1e6:.2f}M (Census: 2.1M)")
print(f"    Poverty: {r_housing['rate_without']:.1%} → {r_housing['rate_with']:.1%}")

# --- School meals (PE-computed) ---
print("\n  School meals (PE-computed):")
free_meals = sim.calc("free_school_meals", period=period).values
reduced_meals = sim.calc("reduced_price_school_meals", period=period).values
meals_spm = free_meals + reduced_meals
r_meals = compute_program_effect(meals_spm, "School meals")
print(f"    Total: ${r_meals['total_benefit_B']:.1f}B (actual: ~$15B)")
print(f"    Children lifted: {r_meals['children_lifted']/1e6:.2f}M")
print(f"    Total people lifted: {r_meals['total_lifted']/1e6:.2f}M (Census: 0.9M)")
print(f"    Poverty: {r_meals['rate_without']:.1%} → {r_meals['rate_with']:.1%}")

# --- WIC (person-level, needs aggregation) ---
print("\n  WIC:")
wic_person_raw = sim.calc("wic", period=period).values
wic_spm = aggregate_person_to_spm(wic_person_raw)
r_wic = compute_program_effect(wic_spm, "WIC")
print(f"    Total: ${r_wic['total_benefit_B']:.1f}B (actual: ~$5B)")
print(f"    Children lifted: {r_wic['children_lifted']/1e6:.2f}M")

# --- Energy subsidies (reported) ---
print("\n  Energy assistance (reported):")
energy_spm = sim.calc("spm_unit_energy_subsidy", period=period).values
r_energy = compute_program_effect(energy_spm, "Energy assistance")
print(f"    Total: ${r_energy['total_benefit_B']:.1f}B (actual: ~$4B)")
print(f"    Children lifted: {r_energy['children_lifted']/1e6:.2f}M")

# --- TANF ---
print("\n  TANF:")
tanf_spm = sim.calc("tanf", period=period).values
r_tanf = compute_program_effect(tanf_spm, "TANF")
print(f"    Total: ${r_tanf['total_benefit_B']:.1f}B (actual: ~$8B)")
print(f"    Children lifted: {r_tanf['children_lifted']/1e6:.2f}M")

# --- Unemployment compensation ---
print("\n  Unemployment compensation:")
uc_person_raw = sim.calc("unemployment_compensation", period=period).values
uc_spm = aggregate_person_to_spm(uc_person_raw)
r_uc = compute_program_effect(uc_spm, "Unemployment comp")
print(f"    Total: ${r_uc['total_benefit_B']:.1f}B (actual: ~$25B)")
print(f"    Children lifted: {r_uc['children_lifted']/1e6:.2f}M")
print(f"    Total people lifted: {r_uc['total_lifted']/1e6:.2f}M (Census: 0.3M)")

# --- EITC (reduces income_tax → reduces spm_unit_taxes → increases net income) ---
print("\n  EITC:")
eitc_spm = sum_tax_units_to_spm("eitc")
r_eitc = compute_program_effect(eitc_spm, "EITC")
print(f"    Total: ${r_eitc['total_benefit_B']:.1f}B (actual: ~$64B)")
print(f"    Children lifted: {r_eitc['children_lifted']/1e6:.2f}M")
print(f"    Poverty: {r_eitc['rate_without']:.1%} → {r_eitc['rate_with']:.1%}")

# --- Refundable CTC ---
print("\n  Refundable CTC:")
try:
    rctc_spm = sum_tax_units_to_spm("refundable_ctc")
    r_rctc = compute_program_effect(rctc_spm, "Refundable CTC")
    print(f"    Total: ${r_rctc['total_benefit_B']:.1f}B (actual: ~$32B)")
    print(f"    Children lifted: {r_rctc['children_lifted']/1e6:.2f}M")
except Exception as e:
    print(f"    ERROR: {e}")
    r_rctc = None

# --- Combined refundable credits ---
print("\n  Combined refundable credits (EITC + CTC):")
if r_rctc:
    combined_spm = eitc_spm + rctc_spm
    r_combined = compute_program_effect(combined_spm, "EITC + refundable CTC")
    print(f"    Total: ${r_combined['total_benefit_B']:.1f}B")
    print(f"    Children lifted: {r_combined['children_lifted']/1e6:.2f}M (Census: 3.7M)")
    print(f"    Poverty: {r_combined['rate_without']:.1%} → {r_combined['rate_with']:.1%}")
else:
    r_combined = compute_program_effect(eitc_spm, "EITC only (CTC unavailable)")
    print(f"    EITC only: {r_combined['children_lifted']/1e6:.2f}M (Census: 3.7M EITC+CTC)")

# ============================================================
# SPM NET INCOME COMPONENTS
# ============================================================
print(f"\n{'='*70}")
print(f"SPM NET INCOME COMPONENTS (Enhanced CPS, weighted totals)")
print(f"{'='*70}")

for var in [
    "spm_unit_market_income", "spm_unit_benefits",
    "spm_unit_taxes", "spm_unit_spm_expenses", "spm_unit_net_income",
]:
    vals = sim.calc(var, period=period).values
    total = weighted_total_spm(vals)
    mean = float(np.average(vals, weights=spm_w))
    print(f"  {var:40s}  total: ${total/1e12:.2f}T  mean: ${mean:,.0f}")

print(f"\n  Benefits breakdown (all annualized by PE when period=YEAR):")
# NOTE: PE annualizes monthly vars automatically when called with period=YEAR.
# Person-level vars need aggregation to SPM level for correct weighting.
spm_level_vars = [
    ("snap", 113), ("free_school_meals", 15),
    ("reduced_price_school_meals", 0), ("tanf", 8),
    ("spm_unit_capped_housing_subsidy", 50),
    ("spm_unit_energy_subsidy", 4), ("spm_unit_broadband_subsidy", 0),
]
person_level_vars = [
    ("social_security", 1300), ("ssi", 56), ("wic", 5),
    ("unemployment_compensation", 25),
]
for var, actual_B in spm_level_vars:
    try:
        vals = sim.calc(var, period=period).values
        total = weighted_total_spm(vals)
        note = f" (actual ~${actual_B}B)" if actual_B else ""
        print(f"    {var:40s}  ${total/1e9:8.1f}B{note}")
    except Exception as e:
        print(f"    {var:40s}  ERROR: {e}")
for var, actual_B in person_level_vars:
    try:
        vals = sim.calc(var, period=period).values
        agg = aggregate_person_to_spm(vals)
        total = weighted_total_spm(agg)
        note = f" (actual ~${actual_B}B)" if actual_B else ""
        print(f"    {var:40s}  ${total/1e9:8.1f}B{note}")
    except Exception as e:
        print(f"    {var:40s}  ERROR: {e}")

print(f"\n  Tax breakdown:")
for var, actual_B in [
    ("spm_unit_federal_tax", 2200), ("spm_unit_payroll_tax", 700),
    ("spm_unit_self_employment_tax", 50), ("spm_unit_state_tax", 450),
]:
    vals = sim.calc(var, period=period).values
    total = weighted_total_spm(vals)
    print(f"    {var:40s}  ${total/1e9:8.1f}B (actual ~${actual_B}B)")

# ============================================================
# DEMOGRAPHIC BREAKDOWNS
# ============================================================
print(f"\n{'='*70}")
print(f"DEMOGRAPHIC BREAKDOWNS: SPM CHILD POVERTY")
print(f"{'='*70}")

# By age group
print(f"\n  By age group:")
print(f"    {'Group':20s}  {'PE Rate':>8s}  {'Census':>8s}  {'Children':>10s}")
print(f"    {'-'*50}")
census_age = {"Under 6": "15.1%", "6-11": "12.6%", "12-17": "12.5%"}
for age_min, age_max, label in [(0, 5, "Under 6"), (6, 11, "6-11"), (12, 17, "12-17")]:
    mask = is_child & (age >= age_min) & (age <= age_max)
    if np.any(mask):
        rate = float(np.average(is_poor[mask], weights=pw[mask]))
        count = float(pw[mask].sum())
        print(f"    {label:20s}  {rate:7.1%}  {census_age[label]:>8s}  {count/1e6:8.1f}M")

# By race/ethnicity
print(f"\n  By race/ethnicity:")
print(f"    {'Group':25s}  {'PE Rate':>8s}  {'Census':>8s}  {'Children':>10s}")
print(f"    {'-'*55}")
census_race = {"White": "~11%", "Black": "~21%", "American Indian": "—", "Asian": "~11%",
               "Hispanic (any race)": "~20%", "Non-Hispanic": "—"}
try:
    cps_race = sim.calc("cps_race", period=period).values
    for code, label in [(1, "White"), (2, "Black"), (3, "American Indian"), (4, "Asian")]:
        mask = is_child & (cps_race == code)
        if np.any(mask):
            rate = float(np.average(is_poor[mask], weights=pw[mask]))
            count = float(pw[mask].sum())
            print(f"    {label:25s}  {rate:7.1%}  {census_race.get(label, '—'):>8s}  {count/1e6:8.1f}M")
except Exception as e:
    print(f"    cps_race: ERROR - {e}")

try:
    is_hispanic = sim.calc("is_hispanic", period=period).values
    for val, label in [(1, "Hispanic (any race)"), (0, "Non-Hispanic")]:
        mask = is_child & (is_hispanic == val)
        if np.any(mask):
            rate = float(np.average(is_poor[mask], weights=pw[mask]))
            count = float(pw[mask].sum())
            print(f"    {label:25s}  {rate:7.1%}  {census_race.get(label, '—'):>8s}  {count/1e6:8.1f}M")
except Exception as e:
    print(f"    Hispanic: ERROR - {e}")

# ============================================================
# RAW CPS COMPARISON
# ============================================================
print(f"\n{'='*70}")
print(f"RAW CPS COMPARISON (3-step waterfall)")
print(f"{'='*70}")

raw_is_child = raw_sim.calc("is_child", period=period).values == 1
raw_pw = raw_sim.calc("person_weight", period=period).values
raw_child_pw = raw_pw[raw_is_child]

# Reported poverty on raw CPS
raw_spm_threshold = raw_sim.calc("spm_unit_spm_threshold", period=period).values
raw_net_reported = raw_sim.calc("spm_unit_net_income_reported", period=period).values
raw_spm_id = raw_sim.calc("spm_unit_id", period=period).values
raw_person_spm_id = raw_sim.calc("person_spm_unit_id", period=period).values
raw_id_to_idx = {int(sid): i for i, sid in enumerate(raw_spm_id)}

raw_threshold_person = np.array([raw_spm_threshold[raw_id_to_idx[int(pid)]] for pid in raw_person_spm_id])
raw_reported_person = np.array([raw_net_reported[raw_id_to_idx[int(pid)]] for pid in raw_person_spm_id])

raw_reported_rate = float(np.average(
    (raw_reported_person < raw_threshold_person).astype(float)[raw_is_child],
    weights=raw_child_pw
))

# PE-computed on raw CPS
raw_net_computed = raw_sim.calc("spm_unit_net_income", period=period).values
raw_computed_person = np.array([raw_net_computed[raw_id_to_idx[int(pid)]] for pid in raw_person_spm_id])
raw_computed_rate = float(np.average(
    (raw_computed_person < raw_threshold_person).astype(float)[raw_is_child],
    weights=raw_child_pw
))

print(f"  Census published:           13.4%")
print(f"  Raw CPS reported:           {raw_reported_rate:.1%}")
print(f"  Raw CPS PE-computed:        {raw_computed_rate:.1%}")
print(f"  Enhanced CPS PE-computed:   {overall_rate:.1%}")
print(f"\n  Gap decomposition:")
print(f"    Census → Raw reported:    {raw_reported_rate - 0.134:+.1%}")
print(f"    Raw reported → PE model:  {raw_computed_rate - raw_reported_rate:+.1%}")
print(f"    Raw → Enhanced weights:   {overall_rate - raw_computed_rate:+.1%}")
print(f"    Total gap (PE vs Census): {overall_rate - 0.134:+.1%}")

# ============================================================
# SUMMARY TABLE
# ============================================================
print(f"\n{'='*70}")
print(f"PROGRAM EFFECTS SUMMARY: PE vs Census")
print(f"{'='*70}")
all_results = [
    (r_snap, "1.4M"),
    (r_ss, "—"),
    (r_ssi, "0.5M"),
    (r_housing, "—"),
    (r_meals, "—"),
    (r_wic, "—"),
    (r_energy, "—"),
    (r_tanf, "—"),
    (r_uc, "—"),
    (r_eitc, "—"),
]
if r_rctc:
    all_results.append((r_rctc, "—"))
    all_results.append((r_combined, "3.7M"))

print(f"  {'Program':35s}  {'PE Kids Lifted':>14s}  {'Census':>10s}  {'PE $':>10s}")
print(f"  {'-'*75}")
for r, census_str in all_results:
    print(f"  {r['label']:35s}  {r['children_lifted']/1e6:12.2f}M  {census_str:>10s}  ${r['total_benefit_B']:8.1f}B")

print(f"\nDone!")
