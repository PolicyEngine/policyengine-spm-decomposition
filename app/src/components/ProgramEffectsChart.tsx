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
import type { ProgramEffect } from "../types/decomposition";
import { PE_COLORS } from "../theme";
import { CHART_MARGIN, CHART_FONT } from "../utils/chartConfig";
import { formatCompact } from "../utils/formatters";

interface ProgramEffectsChartProps {
  programs: ProgramEffect[];
}

interface ChartRow {
  label: string;
  program: string;
  peChildrenLifted: number;
  censusChildrenLifted: number | null;
  totalBenefitB: number;
  rateWith: number;
  rateWithout: number;
}

function buildChartData(programs: ProgramEffect[]): ChartRow[] {
  return programs
    .filter((p) => p.program !== "refundable_credits") // show combined separately
    .map((p) => ({
      label: p.label,
      program: p.program,
      peChildrenLifted: p.children_lifted,
      censusChildrenLifted: p.census_children_lifted_M
        ? p.census_children_lifted_M * 1e6
        : null,
      totalBenefitB: p.total_benefit_B,
      rateWith: p.rate_with,
      rateWithout: p.rate_without,
    }))
    .sort((a, b) => b.peChildrenLifted - a.peChildrenLifted);
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
}) {
  if (!active || !payload?.length) return null;
  const row = (payload[0] as unknown as { payload: ChartRow }).payload;

  return (
    <Box
      p="sm"
      style={{
        background: "white",
        border: `1px solid ${PE_COLORS.gray300}`,
        borderRadius: 6,
        maxWidth: 320,
      }}
    >
      <Text fw={600} size="sm" mb={4}>
        {row.label}
      </Text>
      <Text size="sm">
        PE: lifts {formatCompact(row.peChildrenLifted)} children out of poverty
      </Text>
      {row.censusChildrenLifted && (
        <Text size="sm" c="dimmed">
          Census: lifts {formatCompact(row.censusChildrenLifted)} children
        </Text>
      )}
      <Text size="sm" mt={4}>
        Total spending: ${row.totalBenefitB.toFixed(0)}B
      </Text>
      <Text size="sm" c="dimmed" mt={4}>
        Child poverty: {(row.rateWithout * 100).toFixed(1)}% →{" "}
        {(row.rateWith * 100).toFixed(1)}%
      </Text>
    </Box>
  );
}

export function ProgramEffectsChart({ programs }: ProgramEffectsChartProps) {
  const data = buildChartData(programs);

  // Get the combined refundable credits entry for a callout
  const combined = programs.find((p) => p.program === "refundable_credits");

  return (
    <Box>
      <Title order={2} mb="xs">
        Program effects on child poverty
      </Title>
      <Text size="md" c="dimmed" mb="lg" maw={720}>
        Children lifted out of SPM poverty by each program. For programs with
        Census benchmarks, the comparison shows how PolicyEngine's estimates
        differ. PE bars reflect PE-computed benefits on the enhanced CPS;
        Census bars reflect the Census Bureau's published estimates.
      </Text>

      <ResponsiveContainer width="100%" height={460}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ ...CHART_MARGIN, left: 140, bottom: 20 }}
        >
          <XAxis
            type="number"
            tickFormatter={(v: number) => formatCompact(v)}
            tick={CHART_FONT}
          />
          <YAxis
            dataKey="label"
            type="category"
            tick={{ ...CHART_FONT, fontSize: 12 }}
            width={130}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ ...CHART_FONT, paddingTop: 12 }} />
          <ReferenceLine x={0} stroke={PE_COLORS.gray300} />
          <Bar
            dataKey="peChildrenLifted"
            name="PE estimate"
            fill={PE_COLORS.teal500}
            radius={[0, 4, 4, 0]}
          />
          <Bar
            dataKey="censusChildrenLifted"
            name="Census estimate"
            fill={PE_COLORS.gray500}
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>

      {combined && (
        <Text size="sm" c="dimmed" mt="xs" ta="center">
          Combined EITC + refundable CTC: PE lifts{" "}
          {formatCompact(combined.children_lifted)} children vs Census 3.7M
        </Text>
      )}
    </Box>
  );
}
