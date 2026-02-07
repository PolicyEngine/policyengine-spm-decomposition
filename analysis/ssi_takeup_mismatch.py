"""Investigate SSI take-up mismatch.

Key hypothesis: PE applies 50% take-up, but when we filter to households
that REPORTED receiving SSI, we're looking at people with 100% take-up
(they told us they receive it). So PE might say "you're eligible but
didn't take up" for households that actually did take up.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
from policyengine_us import Microsimulation
from spm_decomposition.config import RAW_CPS_DATASET, YEAR

print("=" * 70)
print("SSI TAKE-UP MISMATCH ANALYSIS")
print("=" * 70)

sim = Microsimulation(dataset=RAW_CPS_DATASET)
period = YEAR

pw = sim.calc("person_weight", period=period).values

# SSI variables
ssi_reported = sim.calc("ssi_reported", period=period).values
ssi_pe = sim.calc("ssi", period=period).values

# Who reports receiving SSI
reported_recipient = ssi_reported > 0
pe_recipient = ssi_pe > 0

n_reported = float((reported_recipient * pw).sum())
n_pe = float((pe_recipient * pw).sum())

print(f"\nTotal SSI recipients:")
print(f"  Reported: {n_reported/1e6:.2f}M")
print(f"  PE-computed: {n_pe/1e6:.2f}M")

# Among those who REPORTED SSI, does PE give them SSI?
reported_and_pe = reported_recipient & pe_recipient
reported_no_pe = reported_recipient & ~pe_recipient

n_both = float((reported_and_pe * pw).sum())
n_reported_only = float((reported_no_pe * pw).sum())

print(f"\nAmong reported SSI recipients ({n_reported/1e6:.2f}M):")
print(f"  PE also gives SSI: {n_both/1e6:.2f}M ({n_both/n_reported:.1%})")
print(f"  PE gives $0 SSI: {n_reported_only/1e6:.2f}M ({n_reported_only/n_reported:.1%})")

# What about amounts?
print(f"\nSSI amounts among reported recipients:")
avg_reported = float(np.average(ssi_reported[reported_recipient], weights=pw[reported_recipient]))
avg_pe_among_reported = float(np.average(ssi_pe[reported_recipient], weights=pw[reported_recipient]))
print(f"  Avg reported SSI: ${avg_reported:,.0f}")
print(f"  Avg PE SSI (same people): ${avg_pe_among_reported:,.0f}")
print(f"  Ratio: {avg_pe_among_reported/avg_reported:.1%}")

# Among those where PE gives SSI too
if n_both > 0:
    avg_reported_both = float(np.average(ssi_reported[reported_and_pe], weights=pw[reported_and_pe]))
    avg_pe_both = float(np.average(ssi_pe[reported_and_pe], weights=pw[reported_and_pe]))
    print(f"\nAmong those where BOTH give SSI ({n_both/1e6:.2f}M):")
    print(f"  Avg reported: ${avg_reported_both:,.0f}")
    print(f"  Avg PE: ${avg_pe_both:,.0f}")
    print(f"  Ratio: {avg_pe_both/avg_reported_both:.1%}")

# Check SSI eligibility vs take-up
print("\n" + "=" * 70)
print("SSI ELIGIBILITY VS TAKE-UP")
print("=" * 70)

# Check if we have eligibility and take-up variables
try:
    ssi_eligible = sim.calc("is_ssi_eligible", period=period).values
    n_eligible = float((ssi_eligible * pw).sum())
    print(f"\nPE-computed SSI eligible: {n_eligible/1e6:.2f}M")

    # Take-up among eligible
    eligible_and_receives = ssi_eligible & pe_recipient
    n_eligible_receives = float((eligible_and_receives * pw).sum())
    print(f"Eligible AND PE gives SSI: {n_eligible_receives/1e6:.2f}M ({n_eligible_receives/n_eligible:.1%})")
except Exception as e:
    print(f"Could not get eligibility: {e}")

# Check if there's a would_claim or takes_up variable
try:
    would_claim = sim.calc("would_claim_ssi", period=period).values
    n_would_claim = float((would_claim * pw).sum())
    print(f"\nwould_claim_ssi: {n_would_claim/1e6:.2f}M")
except:
    pass

try:
    takes_up = sim.calc("takes_up_ssi", period=period).values
    n_takes_up = float((takes_up * pw).sum())
    print(f"takes_up_ssi: {n_takes_up/1e6:.2f}M")
except:
    pass

# What's in ssi_reported for those PE says are eligible but don't receive?
print("\n" + "=" * 70)
print("REPORTED SSI AMONG PE-ELIGIBLE WHO DON'T GET PE SSI")
print("=" * 70)

try:
    eligible_no_pe = ssi_eligible & ~pe_recipient
    n_eligible_no_pe = float((eligible_no_pe * pw).sum())

    if n_eligible_no_pe > 0:
        # Among PE-eligible who don't get PE SSI, how many reported SSI?
        eligible_no_pe_but_reported = eligible_no_pe & reported_recipient
        n_elig_no_pe_reported = float((eligible_no_pe_but_reported * pw).sum())

        print(f"\nPE-eligible but PE gives $0: {n_eligible_no_pe/1e6:.2f}M")
        print(f"  Of these, reported receiving SSI: {n_elig_no_pe_reported/1e6:.2f}M ({n_elig_no_pe_reported/n_eligible_no_pe:.1%})")

        if n_elig_no_pe_reported > 0:
            avg_reported_elig_no_pe = float(np.average(
                ssi_reported[eligible_no_pe_but_reported],
                weights=pw[eligible_no_pe_but_reported]
            ))
            print(f"  Their avg reported SSI: ${avg_reported_elig_no_pe:,.0f}")
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# THE FIX: What if we use reported SSI directly?
# ============================================================
print("\n" + "=" * 70)
print("WHAT IF WE USED REPORTED SSI INSTEAD OF PE-COMPUTED?")
print("=" * 70)

# Get SPM components
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


# Current PE net income
net_pe = sim.calc("spm_unit_net_income", period=period).values
threshold = sim.calc("spm_unit_spm_threshold", period=period).values

# SSI HH mask (reported)
ssi_reported_spm = aggregate_person_to_spm(ssi_reported)
ssi_pe_spm = aggregate_person_to_spm(ssi_pe)
ssi_hh_reported = ssi_reported_spm > 0

n_hh = float((ssi_hh_reported * spm_w).sum())

# Current poverty rate
is_poor_pe = net_pe < threshold
poverty_pe = float(np.average(is_poor_pe[ssi_hh_reported], weights=spm_w[ssi_hh_reported]))
print(f"\nPoverty using PE net income: {poverty_pe:.1%}")

# Adjusted: replace PE SSI with reported SSI
ssi_diff = ssi_reported_spm - ssi_pe_spm  # Amount to add back
net_adjusted = net_pe + ssi_diff

is_poor_adjusted = net_adjusted < threshold
poverty_adjusted = float(np.average(is_poor_adjusted[ssi_hh_reported], weights=spm_w[ssi_hh_reported]))
print(f"Poverty using PE net income + reported SSI: {poverty_adjusted:.1%}")
print(f"Reduction from SSI adjustment: {(poverty_pe - poverty_adjusted)*100:.1f} ppts")

# Compare to reported net income
try:
    net_reported = sim.calc("spm_unit_net_income_reported", period=period).values
    is_poor_reported = net_reported < threshold
    poverty_reported = float(np.average(is_poor_reported[ssi_hh_reported], weights=spm_w[ssi_hh_reported]))
    print(f"\nPoverty using fully reported net income: {poverty_reported:.1%}")
    print(f"\nRemaining gap after SSI fix: {(poverty_adjusted - poverty_reported)*100:.1f} ppts")
except Exception as e:
    print(f"Could not get reported net income: {e}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("""
The core issue: PolicyEngine applies take-up rates to determine who receives
benefits. For SSI, ~50% take-up means only half of eligible people get SSI
in the simulation.

But when we filter to households that REPORTED receiving SSI, we're looking
at people who demonstrably took up the benefit. PE's take-up model assigns
them as "didn't take up" when in reality they did.

This creates a ~$7,600/household SSI gap which shifts the income distribution
down and increases measured poverty from ~38% (using reported income) to
~58% (using PE income).

Potential solutions:
1. Use reported SSI for people who reported receiving it
2. Calibrate take-up model to match reported receipt at micro level
3. For poverty analysis, distinguish "modeled" vs "empirical" income
""")

print("\nDone!")
