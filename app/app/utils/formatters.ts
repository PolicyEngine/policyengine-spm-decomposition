/**
 * Format a decimal as a percentage string.
 * formatPercent(0.134) → "13.4%"
 * formatPercent(0.134, 2) → "13.40%"
 */
export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a number as compact currency.
 * formatCurrency(1724) → "$1,724"
 * formatCurrency(105110) → "$105,110"
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format a pp (percentage point) change.
 * formatPP(0.0414) → "+4.1 pp"
 * formatPP(-0.0037) → "-0.4 pp"
 */
export function formatPP(value: number, decimals = 1): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(decimals)} pp`;
}

/**
 * Format a large number compactly.
 * formatCompact(71555680) → "71.6M"
 */
export function formatCompact(value: number): string {
  if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
  if (Math.abs(value) >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toFixed(0);
}
