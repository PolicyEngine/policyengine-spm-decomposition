"""Decompose income differences for SSI households.

The previous analysis showed that switching from reported to PE-computed
net income adds ~20 ppts to SSI household poverty. This script investigates
which income components drive that gap.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
from policyengine_us import Microsimulation
from spm_decomposition.config import RAW_CPS_DATASET, YEAR

print("=" * 70)
print("SSI HOUSEHOLD INCOME COMPONENT DECOMPOSITION")
print("=" * 70)

# Load raw CPS (cleaner comparison without weight recalibration)
print("\nLoading raw CPS...")
sim = Microsimulation(dataset=RAW_CPS_DATASET)
period = YEAR

# ============================================================
# Setup
# ============================================================
spm_unit_id = sim.calc("spm_unit_id", period=period).values
person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}
n_spm = len(spm_unit_id)

spm_w = np.asarray(sim.calc("spm_unit_spm_threshold", period=period).weights)
pw = sim.calc("person_weight", period=period).values


def aggregate_person_to_spm(person_vals):
    """Sum person-level values to SPM-unit level."""
    spm_agg = np.zeros(n_spm)
    for i, pid in enumerate(person_spm_unit_id):
        idx = spm_id_to_idx[int(pid)]
        spm_agg[idx] += person_vals[i]
    return spm_agg


def weighted_mean_spm(vals, mask=None):
    """Weighted mean at SPM level."""
    if mask is None:
        mask = np.ones(len(vals), dtype=bool)
    return float(np.average(vals[mask], weights=spm_w[mask]))


# ============================================================
# Identify SSI households (using reported SSI)
# ============================================================
ssi_reported = sim.calc("ssi_reported", period=period).values
ssi_reported_spm = aggregate_person_to_spm(ssi_reported)
ssi_hh_mask = ssi_reported_spm > 0

n_ssi_hh = float((ssi_hh_mask * spm_w).sum())
print(f"\nSSI households (reported): {n_ssi_hh/1e6:.2f}M")

# ============================================================
# Compare net income components: reported vs PE-computed
# ============================================================
print("\n" + "=" * 70)
print("NET INCOME COMPONENTS: REPORTED VS PE-COMPUTED")
print("=" * 70)

# SPM net income formula:
# net_income = market_income + benefits - taxes - expenses

# Get reported net income
net_reported = sim.calc("spm_unit_net_income_reported", period=period).values
net_pe = sim.calc("spm_unit_net_income", period=period).values

print(f"\n{'Component':<45} {'Reported':>12} {'PE-computed':>12} {'Gap':>12}")
print("-" * 81)

mean_reported = weighted_mean_spm(net_reported, ssi_hh_mask)
mean_pe = weighted_mean_spm(net_pe, ssi_hh_mask)
print(f"{'SPM Net Income':<45} ${mean_reported:>10,.0f} ${mean_pe:>10,.0f} ${mean_pe - mean_reported:>+10,.0f}")

# Now break down by component
print("\n--- INCOME COMPONENTS ---")

# Market income (should be same)
market_income = sim.calc("spm_unit_market_income", period=period).values
mean_market = weighted_mean_spm(market_income, ssi_hh_mask)
print(f"{'Market income':<45} ${mean_market:>10,.0f}")

# Benefits
print("\n--- BENEFITS (adds to income) ---")
benefits_pe = sim.calc("spm_unit_benefits", period=period).values
mean_benefits_pe = weighted_mean_spm(benefits_pe, ssi_hh_mask)
print(f"{'Total benefits (PE)':<45} ${mean_benefits_pe:>10,.0f}")

# Individual benefit programs - PE computed
benefit_vars_spm = [
    ("snap", "SNAP"),
    ("spm_unit_capped_housing_subsidy", "Housing subsidy"),
    ("spm_unit_energy_subsidy", "Energy subsidy (LIHEAP)"),
    ("free_school_meals", "Free school meals"),
    ("reduced_price_school_meals", "Reduced price school meals"),
    ("tanf", "TANF"),
]

benefit_vars_person = [
    ("ssi", "SSI"),
    ("social_security", "Social Security"),
    ("unemployment_compensation", "Unemployment"),
    ("wic", "WIC"),
]

print(f"\n{'Benefit program':<45} {'PE-computed':>12}")
print("-" * 57)

for var, label in benefit_vars_spm:
    try:
        vals = sim.calc(var, period=period).values
        mean_val = weighted_mean_spm(vals, ssi_hh_mask)
        print(f"  {label:<43} ${mean_val:>10,.0f}")
    except Exception as e:
        print(f"  {label:<43} ERROR: {e}")

for var, label in benefit_vars_person:
    try:
        vals = sim.calc(var, period=period).values
        vals_spm = aggregate_person_to_spm(vals)
        mean_val = weighted_mean_spm(vals_spm, ssi_hh_mask)
        print(f"  {label:<43} ${mean_val:>10,.0f}")
    except Exception as e:
        print(f"  {label:<43} ERROR: {e}")

# Taxes
print("\n--- TAXES (subtracts from income) ---")
taxes_pe = sim.calc("spm_unit_taxes", period=period).values
mean_taxes_pe = weighted_mean_spm(taxes_pe, ssi_hh_mask)
print(f"{'Total taxes (PE)':<45} ${mean_taxes_pe:>10,.0f}")

tax_vars = [
    ("spm_unit_federal_tax", "Federal income tax"),
    ("spm_unit_payroll_tax", "Payroll tax"),
    ("spm_unit_state_tax", "State/local tax"),
]

for var, label in tax_vars:
    try:
        vals = sim.calc(var, period=period).values
        mean_val = weighted_mean_spm(vals, ssi_hh_mask)
        print(f"  {label:<43} ${mean_val:>10,.0f}")
    except Exception as e:
        print(f"  {label:<43} ERROR: {e}")

# Expenses
print("\n--- EXPENSES (subtracts from income) ---")
expenses = sim.calc("spm_unit_spm_expenses", period=period).values
mean_expenses = weighted_mean_spm(expenses, ssi_hh_mask)
print(f"{'SPM expenses (MOOP, childcare, FICA)':<45} ${mean_expenses:>10,.0f}")

# ============================================================
# The key: compare reported vs PE for specific programs
# ============================================================
print("\n" + "=" * 70)
print("REPORTED VS PE-COMPUTED: KEY PROGRAMS")
print("=" * 70)

reported_vars = [
    ("ssi_reported", "ssi", "SSI"),
    ("social_security_reported", "social_security", "Social Security"),
    ("snap_reported", "snap", "SNAP"),
    ("tanf_reported", "tanf", "TANF"),
]

print(f"\n{'Program':<25} {'Reported':>12} {'PE-computed':>12} {'Gap':>12} {'Ratio':>8}")
print("-" * 69)

for reported_var, pe_var, label in reported_vars:
    try:
        # Get reported
        reported_vals = sim.calc(reported_var, period=period).values
        reported_spm = aggregate_person_to_spm(reported_vals)
        mean_reported = weighted_mean_spm(reported_spm, ssi_hh_mask)

        # Get PE-computed
        pe_vals = sim.calc(pe_var, period=period).values
        if pe_var in ["snap", "tanf"]:
            # Already SPM level
            pe_spm = pe_vals
        else:
            pe_spm = aggregate_person_to_spm(pe_vals)
        mean_pe = weighted_mean_spm(pe_spm, ssi_hh_mask)

        gap = mean_pe - mean_reported
        ratio = mean_pe / mean_reported if mean_reported > 0 else float('inf')
        print(f"{label:<25} ${mean_reported:>10,.0f} ${mean_pe:>10,.0f} ${gap:>+10,.0f} {ratio:>7.2f}x")
    except Exception as e:
        print(f"{label:<25} ERROR: {e}")

# ============================================================
# Check tax credits (EITC, CTC) - these reduce tax liability
# ============================================================
print("\n--- TAX CREDITS (reduce tax liability) ---")

# Federal tax includes credits as negative values
# Let's look at EITC and CTC specifically

# Need to map tax unit variables to SPM
tu_id = sim.calc("tax_unit_id", period=period).values
person_tu_id = sim.calc("person_tax_unit_id", period=period).values

tu_to_spm_idx = {}
for i, ptid in enumerate(person_tu_id):
    tid = int(ptid)
    if tid not in tu_to_spm_idx:
        tu_to_spm_idx[tid] = spm_id_to_idx[int(person_spm_unit_id[i])]


def sum_tu_to_spm(tu_vals):
    spm_agg = np.zeros(n_spm)
    for i, tid in enumerate(tu_id):
        spm_idx = tu_to_spm_idx.get(int(tid))
        if spm_idx is not None:
            spm_agg[spm_idx] += tu_vals[i]
    return spm_agg


credit_vars = [
    ("eitc", "EITC"),
    ("ctc", "CTC (total)"),
    ("refundable_ctc", "CTC (refundable portion)"),
]

for var, label in credit_vars:
    try:
        vals = sim.calc(var, period=period).values
        vals_spm = sum_tu_to_spm(vals)
        mean_val = weighted_mean_spm(vals_spm, ssi_hh_mask)
        print(f"  {label:<43} ${mean_val:>10,.0f}")
    except Exception as e:
        print(f"  {label:<43} ERROR: {e}")

# ============================================================
# Check income reported variables that go into market income
# ============================================================
print("\n" + "=" * 70)
print("MARKET INCOME COMPONENTS")
print("=" * 70)

market_vars = [
    ("employment_income", "Employment income"),
    ("self_employment_income", "Self-employment income"),
    ("interest_income", "Interest income"),
    ("dividend_income", "Dividend income"),
    ("rental_income", "Rental income"),
]

for var, label in market_vars:
    try:
        vals = sim.calc(var, period=period).values
        vals_spm = aggregate_person_to_spm(vals)
        mean_val = weighted_mean_spm(vals_spm, ssi_hh_mask)
        print(f"  {label:<43} ${mean_val:>10,.0f}")
    except Exception as e:
        print(f"  {label:<43} ERROR: {e}")

# ============================================================
# Poverty threshold comparison
# ============================================================
print("\n" + "=" * 70)
print("POVERTY THRESHOLD")
print("=" * 70)

threshold = sim.calc("spm_unit_spm_threshold", period=period).values
mean_threshold = weighted_mean_spm(threshold, ssi_hh_mask)
print(f"Mean SPM threshold for SSI HHs: ${mean_threshold:,.0f}")

# Income-to-poverty ratio
ratio_reported = net_reported / threshold
ratio_pe = net_pe / threshold

mean_ratio_reported = weighted_mean_spm(ratio_reported, ssi_hh_mask)
mean_ratio_pe = weighted_mean_spm(ratio_pe, ssi_hh_mask)

print(f"\nMean income-to-poverty ratio:")
print(f"  Using reported net income: {mean_ratio_reported:.2f}")
print(f"  Using PE-computed net income: {mean_ratio_pe:.2f}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY: WHY PE NET INCOME < REPORTED NET INCOME FOR SSI HHs")
print("=" * 70)

print(f"""
Net income gap: ${mean_pe - mean_reported:+,.0f} per SSI household

This gap shifts the income distribution lower, pushing more households
below the poverty line. The gap comes from differences in how PE computes
benefits vs what households reported receiving.

Key programs to investigate:
- SSI: PE computed vs reported
- SNAP: PE computed vs reported
- Tax credits: EITC/CTC computation differences
- Other benefits: Social Security, TANF, etc.
""")

print("\nDone!")
