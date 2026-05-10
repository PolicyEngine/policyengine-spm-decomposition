import { PE_COLORS } from "../theme";

/**
 * Shared chart configuration for Recharts.
 */
export const CHART_MARGIN = { top: 20, right: 30, left: 60, bottom: 60 };

export const CHART_COLORS = {
  primary: PE_COLORS.teal500,
  secondary: PE_COLORS.teal300,
  negative: PE_COLORS.error,
  positive: PE_COLORS.success,
  neutral: PE_COLORS.gray500,
  grid: PE_COLORS.gray300,
  text: PE_COLORS.gray700,
} as const;

export const CHART_FONT = {
  fontFamily: "'Inter', sans-serif",
  fontSize: 12,
} as const;

export const LOGO_URL = "/assets/logos/policyengine/teal.png";
