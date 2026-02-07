# SPM Poverty Decomposition Analysis

This project investigates why PolicyEngine's SPM poverty estimates differ from Census published rates and external analyses like Roosevelt Institute.

## Key findings

### SSI household poverty rate gap

| Source | Baseline poverty |
|--------|------------------|
| Roosevelt Institute | 29.2% |
| Raw CPS - reported income | 38.0% |
| Raw CPS - PE income + reported SSI | 37.6% |
| Raw CPS - PE income | 58.1% |
| Enhanced CPS - PE income | 53.2% |

**The SSI take-up mismatch explains 20+ percentage points of the gap.**

### Root cause: Take-up assignment doesn't match reality

Among people who **reported** receiving SSI (5.48M):
- PE also gives SSI to only **32%** of them
- PE gives $0 SSI to **68%** of reported recipients

This happens because:
1. PE computes 30.6M people are SSI-eligible
2. PE's take-up model assigns ~19% to receive SSI (5.93M)
3. But the assignment is **not calibrated to actual receipt**
4. Result: People who told us they receive SSI get $0 in PE's model

### Impact on poverty measurement

For SSI households (using reported SSI definition):
- **Reported SSI**: avg $10,303/year
- **PE-computed SSI**: avg $2,998/year
- **Gap**: -$7,305/year per household

This income gap shifts the distribution downward, pushing 20+ ppts more households below the poverty line.

### Why reform impacts still match

Both PolicyEngine and Roosevelt show ~18 ppt poverty reduction from SSI Restoration Act.

Reform impacts are computed as **differences** between baseline and reformed scenarios. Both use consistent methodology within their own model, so the relative change is less sensitive to baseline income levels.

## Scripts

| Script | Purpose |
|--------|---------|
| `compute_program_effects.py` | Decompose child poverty by program |
| `decompose_ssi_poverty.py` | SSI household poverty decomposition |
| `decompose_ssi_income.py` | Income component breakdown for SSI HHs |
| `ssi_takeup_mismatch.py` | **Key analysis** - take-up assignment vs reality |
| `check_roosevelt_methodology.py` | Compare different population definitions |

## Potential solutions

1. **Use reported benefits for poverty analysis**: When measuring poverty among benefit recipients, use survey-reported amounts rather than PE-computed.

2. **Calibrate take-up at micro level**: Assign `takes_up_ssi=True` to people who reported receiving SSI in the survey.

3. **Hybrid approach**: Report both "empirical baseline" (using reported income) and "modeled baseline" (using PE income) for transparency.

## Output files

- `output/decomposition.json` - Full decomposition results
- `output/ssi_poverty_decomposition.json` - SSI-specific findings
- `output/state_data.csv` - State-level breakdowns

## Running the analysis

```bash
cd analysis
uv sync
uv run python ssi_takeup_mismatch.py  # Key analysis
uv run python compute_program_effects.py  # Full decomposition
```
