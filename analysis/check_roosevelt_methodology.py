"""Check Roosevelt methodology differences.

Roosevelt shows 29.2% baseline poverty for SSI households.
We show 38% using reported net income on raw CPS.
What explains the remaining 9pp gap?

Possibilities:
1. Different poverty measure (OPM vs SPM)
2. Different population (persons vs HHs, all SSI vs aged/disabled only)
3. Different year/vintage
4. Different income definition
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
from policyengine_us import Microsimulation
from spm_decomposition.config import RAW_CPS_DATASET, YEAR

print("=" * 70)
print("CHECKING METHODOLOGY DIFFERENCES")
print("=" * 70)

sim = Microsimulation(dataset=RAW_CPS_DATASET)
period = YEAR

pw = sim.calc("person_weight", period=period).values

# Setup SPM mapping
spm_unit_id = sim.calc("spm_unit_id", period=period).values
person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}
n_spm = len(spm_unit_id)
spm_w = np.asarray(sim.calc("spm_unit_spm_threshold", period=period).weights)


def aggregate_person_to_spm(person_vals):
    spm_agg = np.zeros(n_spm)
    for i, pid in enumerate(person_spm_unit_id):
        idx = spm_id_to_idx[int(pid)]
        spm_agg[idx] += person_vals[i]
    return spm_agg


def spm_to_person(spm_vals):
    return np.array([spm_vals[spm_id_to_idx[int(pid)]] for pid in person_spm_unit_id])


# Get variables
ssi_reported = sim.calc("ssi_reported", period=period).values
ssi_reported_spm = aggregate_person_to_spm(ssi_reported)

spm_threshold = sim.calc("spm_unit_spm_threshold", period=period).values
net_reported = sim.calc("spm_unit_net_income_reported", period=period).values
net_pe = sim.calc("spm_unit_net_income", period=period).values

is_poor_reported = net_reported < spm_threshold
is_poor_pe = net_pe < spm_threshold

# SSI household mask
ssi_hh = ssi_reported_spm > 0

# ============================================================
# Check different definitions
# ============================================================
print("\n1. HOUSEHOLD-LEVEL POVERTY (our default)")
poverty_hh = float(np.average(is_poor_reported[ssi_hh], weights=spm_w[ssi_hh]))
n_hh = float((ssi_hh * spm_w).sum())
print(f"   SSI households: {n_hh/1e6:.2f}M")
print(f"   Poverty rate: {poverty_hh:.1%}")

# ============================================================
# 2. Person-level poverty among SSI recipients
# ============================================================
print("\n2. PERSON-LEVEL POVERTY (among individuals receiving SSI)")
ssi_recipient = ssi_reported > 0
is_poor_person = spm_to_person(is_poor_reported)
poverty_person = float(np.average(is_poor_person[ssi_recipient], weights=pw[ssi_recipient]))
n_recipients = float((ssi_recipient * pw).sum())
print(f"   SSI recipients: {n_recipients/1e6:.2f}M")
print(f"   Poverty rate: {poverty_person:.1%}")

# ============================================================
# 3. Person-level poverty among people in SSI households
# ============================================================
print("\n3. PERSON-LEVEL POVERTY (among people in SSI households)")
in_ssi_hh = spm_to_person(ssi_hh.astype(float)) > 0
poverty_in_ssi_hh = float(np.average(is_poor_person[in_ssi_hh], weights=pw[in_ssi_hh]))
n_in_ssi_hh = float((in_ssi_hh * pw).sum())
print(f"   People in SSI households: {n_in_ssi_hh/1e6:.2f}M")
print(f"   Poverty rate: {poverty_in_ssi_hh:.1%}")

# ============================================================
# 4. Check OPM (official poverty measure) if available
# ============================================================
print("\n4. OFFICIAL POVERTY MEASURE (OPM)")
try:
    opm_threshold = sim.calc("poverty_line", period=period).values
    # OPM is at tax unit or family level, need to check
    # For now, use person-level
    total_income = sim.calc("household_total_income", period=period).values
    # This might not be right structure, let's try
except Exception as e:
    print(f"   Could not compute OPM: {e}")

# Try in_poverty variable
try:
    in_poverty = sim.calc("in_poverty", period=period).values
    poverty_opm_ssi = float(np.average(in_poverty[ssi_recipient], weights=pw[ssi_recipient]))
    print(f"   in_poverty rate among SSI recipients: {poverty_opm_ssi:.1%}")
except Exception as e:
    print(f"   in_poverty not available: {e}")

# ============================================================
# 5. Deep poverty
# ============================================================
print("\n5. DEEP POVERTY (income < 50% of threshold)")
is_deep_poor = net_reported < (0.5 * spm_threshold)
deep_poverty_hh = float(np.average(is_deep_poor[ssi_hh], weights=spm_w[ssi_hh]))
print(f"   SSI HH deep poverty (reported income): {deep_poverty_hh:.1%}")

# ============================================================
# 6. Check SSI recipient demographics
# ============================================================
print("\n6. SSI RECIPIENT DEMOGRAPHICS")

# Age
age = sim.calc("age", period=period).values
aged_ssi = ssi_recipient & (age >= 65)
non_aged_ssi = ssi_recipient & (age < 65)

n_aged = float((aged_ssi * pw).sum())
n_non_aged = float((non_aged_ssi * pw).sum())

print(f"   Aged (65+) SSI recipients: {n_aged/1e6:.2f}M ({n_aged/n_recipients:.1%})")
print(f"   Non-aged SSI recipients: {n_non_aged/1e6:.2f}M ({n_non_aged/n_recipients:.1%})")

poverty_aged = float(np.average(is_poor_person[aged_ssi], weights=pw[aged_ssi])) if n_aged > 0 else 0
poverty_non_aged = float(np.average(is_poor_person[non_aged_ssi], weights=pw[non_aged_ssi])) if n_non_aged > 0 else 0

print(f"   Poverty rate (aged): {poverty_aged:.1%}")
print(f"   Poverty rate (non-aged): {poverty_non_aged:.1%}")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"""
Roosevelt reports 29.2% poverty for SSI households.
Our rates with reported income:

  Household-level:              {poverty_hh:.1%}
  Person-level (recipients):    {poverty_person:.1%}
  Person-level (in SSI HH):     {poverty_in_ssi_hh:.1%}
  Aged SSI recipients:          {poverty_aged:.1%}
  Non-aged SSI recipients:      {poverty_non_aged:.1%}

The gap could be explained by:
1. Roosevelt may be using OPM instead of SPM
2. Different unit of analysis
3. Different year (their 2024 might be different vintage)
4. Income definition differences

Note: Roosevelt's source says they use CPS ASEC and SPM unit analysis.
The 29.2% baseline might use different SPM adjustments or population.
""")

print("\nDone!")
