"""Configuration: dataset paths, Census benchmarks, state codes."""

YEAR = 2024

# Dataset paths on HuggingFace
RAW_CPS_DATASET = "hf://policyengine/policyengine-us-data/cps_2023.h5"
ENHANCED_CPS_DATASET = "hf://policyengine/policyengine-us-data/enhanced_cps_2024.h5"

# Census published SPM child poverty rate for 2024
# Source: Census Bureau, "Income and Poverty in the United States: 2024"
CENSUS_PUBLISHED_CHILD_POVERTY_2024 = 0.134

# State codes (50 states + DC)
STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL",
    "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA",
    "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE",
    "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV",
    "WY",
]

STATE_DATASET_TEMPLATE = "hf://policyengine/policyengine-us-data/states/{state}.h5"

# Household type grouping for weight rebalancing analysis
# Income quintile × family structure (single parent vs married/other)
INCOME_QUINTILE_LABELS = ["Q1", "Q2", "Q3", "Q4", "Q5"]
FAMILY_STRUCTURE_LABELS = ["single parent", "married"]
