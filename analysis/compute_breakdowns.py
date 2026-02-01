"""Compare PE demographic/program breakdowns against Census publication benchmarks."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
from policyengine_us import Microsimulation
from spm_decomposition.config import ENHANCED_CPS_DATASET, RAW_CPS_DATASET, YEAR
from spm_decomposition.poverty import _map_spm_to_person

print("Loading enhanced CPS...")
sim = Microsimulation(dataset=ENHANCED_CPS_DATASET)
print("Loading raw CPS...")
raw_sim = Microsimulation(dataset=RAW_CPS_DATASET)

period = YEAR

# --- Person-level variables ---
is_child = sim.calc("is_child", period=period).values == 1
pw = sim.calc("person_weight", period=period).values
age = sim.calc("age", period=period).values
pip = sim.calc("person_in_poverty", period=period).values  # PE-computed

# SPM threshold and net income at SPM-unit level
spm_threshold = sim.calc("spm_unit_spm_threshold", period=period).values
spm_net_income = sim.calc("spm_unit_net_income", period=period).values

# Map SPM-unit level to person level
spm_unit_id = sim.calc("spm_unit_id", period=period).values
person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}

def spm_to_person(spm_vals):
    return np.array([spm_vals[spm_id_to_idx[int(pid)]] for pid in person_spm_unit_id])

person_threshold = spm_to_person(spm_threshold)
person_net_income = spm_to_person(spm_net_income)

# ============================================================
# 1. Overall child poverty rate
# ============================================================
print("\n" + "="*70)
print("OVERALL SPM CHILD POVERTY")
print("="*70)
child_pw = pw[is_child]
pe_rate = float(np.average(pip[is_child], weights=child_pw))
total_children = float(child_pw.sum())
children_in_poverty = float((pip[is_child] * child_pw).sum())

print(f"  PE-computed:      {pe_rate:.1%} ({children_in_poverty/1e6:.1f}M of {total_children/1e6:.1f}M children)")
print(f"  Census published: 13.4%")

# ============================================================
# 2. Program effects: how many children each program lifts out
#    Methodology: remove each benefit, recalculate poverty
# ============================================================
print("\n" + "="*70)
print("PROGRAM EFFECTS ON CHILD SPM POVERTY")
print("(PE vs Census: how many children each program lifts out of poverty)")
print("="*70)

programs = {
    "spm_unit_snap": "SNAP",
    "spm_unit_capped_housing_subsidy": "Housing subsidies",
    "spm_unit_school_lunch_subsidy": "School lunch",
    "spm_unit_energy_subsidy": "Energy assistance (LIHEAP)",
    "spm_unit_wic": "WIC",
}

# Also compute the effect of refundable tax credits and social security
# These need different approaches

# For SPM-unit level benefits: subtract from net income, check if below threshold
for var_name, label in programs.items():
    try:
        benefit_spm = sim.calc(var_name, period=period).values
        benefit_person = spm_to_person(benefit_spm)
        
        # Net income without this benefit
        net_income_without = person_net_income - benefit_person
        poor_without = (net_income_without < person_threshold).astype(float)
        poor_with = (person_net_income < person_threshold).astype(float)
        
        # Children lifted out
        lifted_children = float(((poor_without - poor_with) * pw)[is_child].sum())
        rate_without = float(np.average(poor_without[is_child], weights=child_pw))
        rate_with = float(np.average(poor_with[is_child], weights=child_pw))
        
        print(f"\n  {label} ({var_name}):")
        print(f"    Child poverty without: {rate_without:.1%}")
        print(f"    Child poverty with:    {rate_with:.1%}")
        print(f"    Children lifted out:   {lifted_children/1e6:.2f}M")
    except Exception as e:
        print(f"\n  {label}: ERROR - {e}")

# Social Security - person level
print("\n  --- Person-level programs ---")
try:
    ss = sim.calc("social_security", period=period).values
    # Social security is person-level, need to aggregate to SPM unit then back
    # Simpler: subtract from person's contribution to SPM net income
    # Actually, the proper way: sum SS at SPM unit level, subtract from net income
    ss_by_spm = np.zeros(len(spm_unit_id))
    for i, pid in enumerate(person_spm_unit_id):
        idx = spm_id_to_idx[int(pid)]
        ss_by_spm[idx] += ss[i]
    ss_person = spm_to_person(ss_by_spm)
    
    net_without_ss = person_net_income - ss_person
    poor_without_ss = (net_without_ss < person_threshold).astype(float)
    poor_with_ss = (person_net_income < person_threshold).astype(float)
    
    lifted_ss = float(((poor_without_ss - poor_with_ss) * pw)[is_child].sum())
    rate_without_ss = float(np.average(poor_without_ss[is_child], weights=child_pw))
    
    print(f"\n  Social Security:")
    print(f"    Child poverty without: {rate_without_ss:.1%}")
    print(f"    Children lifted out:   {lifted_ss/1e6:.2f}M")
    print(f"    Census says:           ~part of 28.7M total people lifted")
except Exception as e:
    print(f"\n  Social Security: ERROR - {e}")

# SSI
try:
    ssi = sim.calc("ssi", period=period).values
    ssi_by_spm = np.zeros(len(spm_unit_id))
    for i, pid in enumerate(person_spm_unit_id):
        idx = spm_id_to_idx[int(pid)]
        ssi_by_spm[idx] += ssi[i]
    ssi_person = spm_to_person(ssi_by_spm)
    
    net_without_ssi = person_net_income - ssi_person
    poor_without_ssi = (net_without_ssi < person_threshold).astype(float)
    
    lifted_ssi = float(((poor_without_ssi - (person_net_income < person_threshold).astype(float)) * pw)[is_child].sum())
    rate_without_ssi = float(np.average(poor_without_ssi[is_child], weights=child_pw))
    
    print(f"\n  SSI:")
    print(f"    Child poverty without: {rate_without_ssi:.1%}")
    print(f"    Children lifted out:   {lifted_ssi/1e6:.2f}M")
except Exception as e:
    print(f"\n  SSI: ERROR - {e}")

# EITC - tax unit level
try:
    eitc_tu = sim.calc("eitc", period=period).values
    tu_id = sim.calc("tax_unit_id", period=period).values
    person_tu_id = sim.calc("person_tax_unit_id", period=period).values
    tu_id_to_idx = {int(tid): i for i, tid in enumerate(tu_id)}
    
    # Aggregate EITC to SPM unit level
    eitc_by_spm = np.zeros(len(spm_unit_id))
    for i, pid in enumerate(person_spm_unit_id):
        spm_idx = spm_id_to_idx[int(pid)]
        tu_idx = tu_id_to_idx[int(person_tu_id[i])]
        # Only add once per tax unit per SPM unit (use person 0 of each TU)
    
    # Better: map EITC from tax unit to person, then aggregate to SPM unit
    eitc_person = np.array([eitc_tu[tu_id_to_idx[int(ptid)]] for ptid in person_tu_id])
    # But this double-counts within tax units. Need unique TU per SPM unit.
    # Simplest: use the spm_unit_eitc variable if it exists
    spm_eitc = sim.calc("spm_unit_eitc", period=period).values
    spm_eitc_person = spm_to_person(spm_eitc)
    
    net_without_eitc = person_net_income - spm_eitc_person
    poor_without_eitc = (net_without_eitc < person_threshold).astype(float)
    
    lifted_eitc = float(((poor_without_eitc - (person_net_income < person_threshold).astype(float)) * pw)[is_child].sum())
    rate_without_eitc = float(np.average(poor_without_eitc[is_child], weights=child_pw))
    
    print(f"\n  EITC (spm_unit_eitc):")
    print(f"    Child poverty without: {rate_without_eitc:.1%}")
    print(f"    Children lifted out:   {lifted_eitc/1e6:.2f}M")
    print(f"    Census says:           ~3.7M children (EITC + refundable CTC combined)")
except Exception as e:
    print(f"\n  EITC: ERROR - {e}")

# Refundable tax credits combined
try:
    spm_actc = sim.calc("spm_unit_actc", period=period).values
    actc_person = spm_to_person(spm_actc)
    
    net_without_refundable = person_net_income - spm_eitc_person - actc_person
    poor_without_ref = (net_without_refundable < person_threshold).astype(float)
    
    lifted_ref = float(((poor_without_ref - (person_net_income < person_threshold).astype(float)) * pw)[is_child].sum())
    rate_without_ref = float(np.average(poor_without_ref[is_child], weights=child_pw))
    
    print(f"\n  Refundable tax credits (EITC + ACTC):")
    print(f"    Child poverty without: {rate_without_ref:.1%}")
    print(f"    Children lifted out:   {lifted_ref/1e6:.2f}M")
    print(f"    Census says:           3.7M children")
except Exception as e:
    print(f"\n  Refundable tax credits: ERROR - {e}")

# ============================================================
# 3. Demographic breakdowns
# ============================================================
print("\n" + "="*70)
print("DEMOGRAPHIC BREAKDOWNS OF SPM CHILD POVERTY")
print("="*70)

# By age group
print("\n  By age group:")
for age_min, age_max, label in [(0, 5, "Under 6"), (6, 11, "6-11"), (12, 17, "12-17")]:
    mask = is_child & (age >= age_min) & (age <= age_max)
    if np.any(mask):
        rate = float(np.average(pip[mask], weights=pw[mask]))
        count = float(pw[mask].sum())
        print(f"    {label}: {rate:.1%} ({count/1e6:.1f}M children)")

# By race
print("\n  By race (PE-computed SPM child poverty):")
try:
    race = sim.calc("race", period=period).values
    # Race categories vary - let's see what values exist
    unique_races = np.unique(race)
    print(f"    Race values: {unique_races[:10]}")
except:
    pass

try:
    cps_race = sim.calc("cps_race", period=period).values
    # CPS race: 1=White, 2=Black, 3=American Indian, 4=Asian, etc.
    race_labels = {1: "White", 2: "Black", 3: "American Indian", 4: "Asian"}
    for code, label in race_labels.items():
        mask = is_child & (cps_race == code)
        if np.any(mask):
            rate = float(np.average(pip[mask], weights=pw[mask]))
            count = float(pw[mask].sum())
            print(f"    {label}: {rate:.1%} ({count/1e6:.1f}M)")
except Exception as e:
    print(f"    cps_race: ERROR - {e}")

try:
    is_hispanic = sim.calc("is_hispanic", period=period).values
    mask_h = is_child & (is_hispanic == 1)
    mask_nh = is_child & (is_hispanic == 0)
    if np.any(mask_h):
        rate_h = float(np.average(pip[mask_h], weights=pw[mask_h]))
        rate_nh = float(np.average(pip[mask_nh], weights=pw[mask_nh]))
        print(f"    Hispanic: {rate_h:.1%} ({float(pw[mask_h].sum())/1e6:.1f}M)")
        print(f"    Non-Hispanic: {rate_nh:.1%} ({float(pw[mask_nh].sum())/1e6:.1f}M)")
except Exception as e:
    print(f"    Hispanic: ERROR - {e}")

# ============================================================
# 4. Same breakdowns on RAW CPS (reported poverty)
# ============================================================
print("\n" + "="*70)
print("RAW CPS REPORTED POVERTY (for comparison)")
print("="*70)

raw_is_child = raw_sim.calc("is_child", period=period).values == 1
raw_pw = raw_sim.calc("person_weight", period=period).values

# Reported poverty on raw CPS
raw_spm_threshold = raw_sim.calc("spm_unit_spm_threshold", period=period).values
raw_net_reported = raw_sim.calc("spm_unit_net_income_reported", period=period).values
raw_spm_id = raw_sim.calc("spm_unit_id", period=period).values
raw_person_spm_id = raw_sim.calc("person_spm_unit_id", period=period).values
raw_id_to_idx = {int(sid): i for i, sid in enumerate(raw_spm_id)}

raw_poor_spm = (raw_net_reported < raw_spm_threshold).astype(float)
raw_poor_person = np.array([raw_poor_spm[raw_id_to_idx[int(pid)]] for pid in raw_person_spm_id])

raw_child_pw = raw_pw[raw_is_child]
raw_rate = float(np.average(raw_poor_person[raw_is_child], weights=raw_child_pw))
print(f"  Raw CPS reported child poverty: {raw_rate:.1%}")
print(f"  Census published:               13.4%")

# ============================================================
# 5. What if we use the CPS-reported SPM resources on the enhanced CPS?
# ============================================================
print("\n" + "="*70)
print("ENHANCED CPS: PE net income vs reported net income")
print("="*70)
try:
    spm_net_reported = sim.calc("spm_unit_net_income_reported", period=period).values
    reported_person = spm_to_person(spm_net_reported)
    
    poor_reported = (reported_person < person_threshold).astype(float)
    rate_reported = float(np.average(poor_reported[is_child], weights=child_pw))
    
    print(f"  Enhanced CPS, PE-computed net income:  {pe_rate:.1%}")
    print(f"  Enhanced CPS, CPS-reported net income: {rate_reported:.1%}")
    print(f"  (Reported is roughly random from PUF copies, so not meaningful)")
except Exception as e:
    print(f"  ERROR: {e}")

# Net income components
print("\n  PE net income components (mean across all SPM units):")
for var in ["spm_unit_market_income", "spm_unit_benefits", "spm_unit_taxes", "spm_unit_net_income"]:
    try:
        vals = sim.calc(var, period=period).values
        w = sim.calc(var, period=period).weights
        mean_val = float(np.average(vals, weights=np.asarray(w)))
        print(f"    {var}: ${mean_val:,.0f}")
    except Exception as e:
        print(f"    {var}: ERROR - {e}")

print("\nDone!")
