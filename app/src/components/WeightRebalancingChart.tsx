import { Box, Title, Text } from "@mantine/core";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { WeightRebalancingGroup } from "../types/decomposition";
import { PE_COLORS } from "../theme";
import { CHART_MARGIN, CHART_FONT } from "../utils/chartConfig";
import { formatPercent } from "../utils/formatters";

interface WeightRebalancingChartProps {
  groups: WeightRebalancingGroup[];
}

interface ChartRow {
  label: string;
  rawPovertyRate: number;
  enhancedPovertyRate: number;
  childShareDelta: number;
}

function buildChartData(groups: WeightRebalancingGroup[]): ChartRow[] {
  return groups.map((g) => ({
    label: g.label,
    rawPovertyRate: g.raw_cps_poverty_rate,
    enhancedPovertyRate: g.enhanced_cps_poverty_rate,
    childShareDelta: g.enhanced_cps_child_share - g.raw_cps_child_share,
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

  return (
    <Box
      p="sm"
      style={{
        background: "white",
        border: `1px solid ${PE_COLORS.gray300}`,
        borderRadius: 6,
        maxWidth: 260,
      }}
    >
      <Text fw={600} size="sm" mb={4}>
        {label}
      </Text>
      {payload.map((entry, i) => (
        <Text key={i} size="sm" style={{ color: entry.color }}>
          {entry.name}: {formatPercent(entry.value)}
        </Text>
      ))}
    </Box>
  );
}

export function WeightRebalancingChart({
  groups,
}: WeightRebalancingChartProps) {
  const data = buildChartData(groups);

  return (
    <Box>
      <Title order={2} mb="xs">
        Weight rebalancing impact
      </Title>
      <Text size="md" c="dimmed" mb="lg" maw={720}>
        Comparing the SPM child poverty rate by household type between the
        raw CPS and the enhanced CPS (recalibrated to IRS targets). The
        enhanced CPS shifts weight toward lower-income households with
        children, raising the overall poverty rate.
      </Text>

      <ResponsiveContainer width="100%" height={420}>
        <BarChart
          data={data}
          margin={{ ...CHART_MARGIN, bottom: 80 }}
        >
          <XAxis
            dataKey="label"
            tick={{ ...CHART_FONT, fontSize: 11 }}
            interval={0}
            angle={-35}
            textAnchor="end"
            height={80}
          />
          <YAxis
            tickFormatter={(v: number) => formatPercent(v)}
            tick={CHART_FONT}
            domain={[0, "auto"]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ ...CHART_FONT, paddingTop: 12 }}
          />
          <Bar
            dataKey="rawPovertyRate"
            name="Raw CPS"
            fill={PE_COLORS.gray500}
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="enhancedPovertyRate"
            name="Enhanced CPS"
            fill={PE_COLORS.teal500}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}
