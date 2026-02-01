import { Box, Title, Text } from "@mantine/core";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { TaxGapDecile } from "../types/decomposition";
import { PE_COLORS } from "../theme";
import { CHART_MARGIN, CHART_FONT } from "../utils/chartConfig";
import { formatCurrency } from "../utils/formatters";

interface TaxGapChartProps {
  deciles: TaxGapDecile[];
}

interface ChartRow {
  label: string;
  decile: number;
  peComputedTax: number;
  reportedTax: number;
  gap: number;
  meanIncome: number;
}

function buildChartData(deciles: TaxGapDecile[]): ChartRow[] {
  return deciles.map((d) => ({
    label: `D${d.decile}`,
    decile: d.decile,
    peComputedTax: d.pe_federal_tax,
    reportedTax: d.reported_federal_tax,
    gap: d.gap,
    meanIncome: d.mean_income,
  }));
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  // Access the full data row from the first payload item
  const row = (
    payload[0] as unknown as { payload: ChartRow }
  ).payload;

  return (
    <Box
      p="sm"
      style={{
        background: "white",
        border: `1px solid ${PE_COLORS.gray300}`,
        borderRadius: 6,
        maxWidth: 300,
      }}
    >
      <Text fw={600} size="sm" mb={4}>
        Income decile {label} (mean: {formatCurrency(row.meanIncome)})
      </Text>
      {payload.map((entry, i) => (
        <Text key={i} size="sm" style={{ color: entry.color }}>
          {entry.name}: {formatCurrency(entry.value)}
        </Text>
      ))}
      <Text size="sm" fw={500} mt={4} c="dimmed">
        Gap: {formatCurrency(row.gap)}
      </Text>
    </Box>
  );
}

export function TaxGapChart({ deciles }: TaxGapChartProps) {
  const data = buildChartData(deciles);

  return (
    <Box>
      <Title order={2} mb="xs">
        Federal tax gap by income decile
      </Title>
      <Text size="md" c="dimmed" mb="lg" maw={720}>
        Mean federal tax per household as computed by PolicyEngine vs. as
        reported in the CPS, broken out by income decile. The top decile
        shows the largest gap: PolicyEngine computes substantially higher
        taxes, reflecting PUF-imputed capital gains and other income
        sources.
      </Text>

      <ResponsiveContainer width="100%" height={420}>
        <BarChart
          data={data}
          margin={{ ...CHART_MARGIN, bottom: 40 }}
        >
          <XAxis
            dataKey="label"
            tick={CHART_FONT}
          />
          <YAxis
            tickFormatter={(v: number) => formatCurrency(v)}
            tick={{ ...CHART_FONT, fontSize: 11 }}
            width={80}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ ...CHART_FONT, paddingTop: 12 }} />
          <ReferenceLine y={0} stroke={PE_COLORS.gray300} />
          <Bar
            dataKey="peComputedTax"
            name="PE-computed tax"
            fill={PE_COLORS.teal500}
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="reportedTax"
            name="CPS-reported tax"
            fill={PE_COLORS.gray500}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}
