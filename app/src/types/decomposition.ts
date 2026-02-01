export interface WaterfallStep {
  label: string;
  value: number; // poverty rate as decimal (e.g. 0.134)
}

export interface WaterfallDelta {
  from: string;
  to: string;
  delta: number; // pp change as decimal
  explanation: string;
}

export interface WeightRebalancingGroup {
  label: string; // e.g. "Low-income, 2+ children"
  raw_cps_poverty_rate: number;
  enhanced_cps_poverty_rate: number;
  raw_cps_child_share: number; // share of total children
  enhanced_cps_child_share: number;
}

export interface TaxGapDecile {
  decile: number;
  mean_income: number;
  pe_federal_tax: number;
  reported_federal_tax: number;
  gap: number;
}

export interface StateResult {
  state: string;
  reported_child_poverty: number;
  computed_child_poverty: number;
  total_children: number;
}

export interface DecompositionMetadata {
  generated_at: string;
  policyengine_us_version: string;
  raw_cps_dataset: string;
  enhanced_cps_dataset: string;
  total_runtime_seconds: number;
}

export interface DecompositionData {
  waterfall: {
    steps: WaterfallStep[];
    deltas: WaterfallDelta[];
  };
  weight_rebalancing: {
    groups: WeightRebalancingGroup[];
  };
  tax_gap_by_decile: TaxGapDecile[];
  state_results: StateResult[];
  metadata: DecompositionMetadata;
}
