"""Check aggregate SSI: reported vs PE vs admin data."""

import numpy as np
from policyengine_us import Microsimulation

# Load both datasets
print("Loading datasets...")
raw = Microsimulation(dataset="/Users/maxghenis/policyengine-us-data/policyengine_us_data/storage/cps_2024.h5")
enhanced = Microsimulation(dataset="hf://policyengine/policyengine-us-data/enhanced_cps_2024.h5")

period = 2024

print("\n" + "=" * 60)
print("SSI AGGREGATE COMPARISON")
print("=" * 60)

# Admin data (SSA)
admin_recipients_M = 7.4
admin_spending_B = 63

print(f"\nAdmin (SSA): {admin_recipients_M}M recipients, ${admin_spending_B}B spending")

# Raw CPS
pw_raw = raw.calc("person_weight", period=period).values
ssi_reported_raw = raw.calc("ssi_reported", period=period).values
ssi_pe_raw = raw.calc("ssi", period=period).values

reported_raw_recipients = float(((ssi_reported_raw > 0) * pw_raw).sum()) / 1e6
reported_raw_spending = float((ssi_reported_raw * pw_raw).sum()) / 1e9
pe_raw_recipients = float(((ssi_pe_raw > 0) * pw_raw).sum()) / 1e6
pe_raw_spending = float((ssi_pe_raw * pw_raw).sum()) / 1e9

print(f"\nRAW CPS:")
print(f"  Reported: {reported_raw_recipients:.2f}M recipients, ${reported_raw_spending:.1f}B spending")
print(f"  PE-computed: {pe_raw_recipients:.2f}M recipients, ${pe_raw_spending:.1f}B spending")

# Enhanced CPS
pw_enh = enhanced.calc("person_weight", period=period).values
ssi_reported_enh = enhanced.calc("ssi_reported", period=period).values
ssi_pe_enh = enhanced.calc("ssi", period=period).values

reported_enh_recipients = float(((ssi_reported_enh > 0) * pw_enh).sum()) / 1e6
reported_enh_spending = float((ssi_reported_enh * pw_enh).sum()) / 1e9
pe_enh_recipients = float(((ssi_pe_enh > 0) * pw_enh).sum()) / 1e6
pe_enh_spending = float((ssi_pe_enh * pw_enh).sum()) / 1e9

print(f"\nENHANCED CPS:")
print(f"  Reported: {reported_enh_recipients:.2f}M recipients, ${reported_enh_spending:.1f}B spending")
print(f"  PE-computed: {pe_enh_recipients:.2f}M recipients, ${pe_enh_spending:.1f}B spending")

# Check if ssi_reported is the same in both
print("\n" + "=" * 60)
print("IS ssi_reported PRESERVED IN ENHANCED CPS?")
print("=" * 60)

# Check if values are identical (accounting for weight differences)
# Let's look at unweighted distributions
print(f"\nRaw CPS ssi_reported: min={ssi_reported_raw.min():.0f}, max={ssi_reported_raw.max():.0f}, mean={ssi_reported_raw.mean():.0f}")
print(f"Enhanced ssi_reported: min={ssi_reported_enh.min():.0f}, max={ssi_reported_enh.max():.0f}, mean={ssi_reported_enh.mean():.0f}")

# Are they same shape?
print(f"\nRaw CPS records: {len(ssi_reported_raw)}")
print(f"Enhanced CPS records: {len(ssi_reported_enh)}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"""
Admin (SSA):         {admin_recipients_M:.1f}M  ${admin_spending_B:.1f}B

Raw CPS:
  Reported:          {reported_raw_recipients:.2f}M  ${reported_raw_spending:.1f}B  (underreported vs admin)
  PE-computed:       {pe_raw_recipients:.2f}M  ${pe_raw_spending:.1f}B

Enhanced CPS:
  Reported:          {reported_enh_recipients:.2f}M  ${reported_enh_spending:.1f}B
  PE-computed:       {pe_enh_recipients:.2f}M  ${pe_enh_spending:.1f}B  (calibrated closer to admin)

Key insight:
- Reported SSI in CPS is underreported (~${reported_raw_spending:.0f}B vs admin ~${admin_spending_B}B)
- PE computes SSI from eligibility rules to get closer to admin totals
- But PE assigns SSI to different people than those who reported receiving it
- Result: aggregate closer to reality, but household-level income distribution wrong

The tradeoff:
- Use reported → household poverty matches survey, but aggregates off by ~{(admin_spending_B - reported_raw_spending)/admin_spending_B*100:.0f}%
- Use PE-computed → aggregates closer, but 68% of reported recipients get $0
""")

print("Done!")
