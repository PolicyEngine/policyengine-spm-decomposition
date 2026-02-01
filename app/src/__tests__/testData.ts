import type { DecompositionData } from "../types/decomposition";

export const TEST_DATA: DecompositionData = {
  waterfall: {
    steps: [
      { label: "Census published (2024)", value: 0.134 },
      { label: "Raw CPS reported (2024)", value: 0.1354 },
      { label: "Raw CPS PE-computed (2024)", value: 0.139 },
      { label: "Enhanced CPS reported (2024)", value: 0.1844 },
      { label: "Enhanced CPS PE-computed (2024)", value: 0.2258 },
    ],
    deltas: [
      {
        from: "Census published (2024)",
        to: "Raw CPS reported (2024)",
        delta: 0.0014,
        explanation:
          "Public-use ASEC vs internal Census file (privacy edits, minor corrections)",
      },
      {
        from: "Raw CPS reported (2024)",
        to: "Raw CPS PE-computed (2024)",
        delta: 0.0036,
        explanation: "PE tax/benefit modeling on raw CPS data",
      },
      {
        from: "Raw CPS PE-computed (2024)",
        to: "Enhanced CPS reported (2024)",
        delta: 0.0454,
        explanation: "Enhanced CPS weight recalibration to IRS SOI targets",
      },
      {
        from: "Enhanced CPS reported (2024)",
        to: "Enhanced CPS PE-computed (2024)",
        delta: 0.0414,
        explanation:
          "PE tax/benefit modeling on enhanced CPS (PUF-imputed income taxed higher)",
      },
    ],
  },
  weight_rebalancing: {
    groups: [
      {
        label: "Q1, single parent",
        raw_cps_poverty_rate: 0.42,
        enhanced_cps_poverty_rate: 0.51,
        raw_cps_child_share: 0.08,
        enhanced_cps_child_share: 0.1,
      },
      {
        label: "Q1, married",
        raw_cps_poverty_rate: 0.28,
        enhanced_cps_poverty_rate: 0.35,
        raw_cps_child_share: 0.05,
        enhanced_cps_child_share: 0.07,
      },
      {
        label: "Q2, single parent",
        raw_cps_poverty_rate: 0.18,
        enhanced_cps_poverty_rate: 0.22,
        raw_cps_child_share: 0.1,
        enhanced_cps_child_share: 0.11,
      },
    ],
  },
  tax_gap_by_decile: [
    {
      decile: 1,
      mean_income: -12371,
      pe_federal_tax: -269,
      reported_federal_tax: 1724,
      gap: -1993,
    },
    {
      decile: 2,
      mean_income: 15336,
      pe_federal_tax: -5845,
      reported_federal_tax: -6429,
      gap: 584,
    },
    {
      decile: 10,
      mean_income: 722831,
      pe_federal_tax: 184718,
      reported_federal_tax: 79608,
      gap: 105110,
    },
  ],
  state_results: [
    {
      state: "CA",
      reported_child_poverty: 0.15,
      computed_child_poverty: 0.24,
      total_children: 8500000,
    },
    {
      state: "TX",
      reported_child_poverty: 0.16,
      computed_child_poverty: 0.25,
      total_children: 7200000,
    },
    {
      state: "NY",
      reported_child_poverty: 0.14,
      computed_child_poverty: 0.22,
      total_children: 4100000,
    },
  ],
  metadata: {
    generated_at: "2026-01-31T00:00:00Z",
    policyengine_us_version: "1.534.5",
    raw_cps_dataset: "hf://policyengine/policyengine-us-data/cps_2023.h5",
    enhanced_cps_dataset:
      "hf://policyengine/policyengine-us-data/enhanced_cps_2024.h5",
    total_runtime_seconds: 0,
  },
};

// Data with _WARNING field to test sample data banner
export const TEST_DATA_WITH_WARNING = {
  ...TEST_DATA,
  _WARNING: "SAMPLE DATA - Will be replaced by Python package output.",
};
