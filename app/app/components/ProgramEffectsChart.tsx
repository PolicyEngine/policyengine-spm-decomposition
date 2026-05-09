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
import type { ProgramEffect, PopulationView } from "../types/decomposition";
import { PE_COLORS } from "../theme";
import { CHART_MARGIN, CHART_FONT } from "../utils/chartConfig";
import { formatCompact } from "../utils/formatters";

interface ProgramEffectsChartProps {
  programs: ProgramEffect[];
  populationView: PopulationView;
}

interface ChartRow {
  label: string;
  program: string;
  lifted: number;
  censusLifted: number | null;
  totalBenefitB: number;
  rateWith: number;
  rateWithout: number;
}

function buildChartData(
  programs: ProgramEffect[],
  populationView: PopulationView,
): ChartRow[] {
  return programs
    .filter((p) => p.program !== "refundable_credits")
    .map((p) => ({
      label: p.label,
      program: p.program,
      lifted:
        populationView === "all_persons" ? p.total_lifted : p.children_lifted,
      censusLifted:
        populationView === "children" && p.census_children_lifted_M
          ? p.census_children_lifted_M * 1e6
          : null,
      totalBenefitB: p.total_benefit_B,
      rateWith:
        populationView === "all_persons" && p.all_persons_rate_with != null
          ? p.all_persons_rate_with
          : p.rate_with,
      rateWithout:
        populationView === "all_persons" && p.all_persons_rate_without != null
          ? p.all_persons_rate_without
          : p.rate_without,
    }))
    .sort((a, b) => b.lifted - a.lifted);
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
        Lifts {formatCompact(row.lifted)} people out of poverty
      </Text>
      {row.censusLifted && (
        <Text size="sm" c="dimmed">
          Census: lifts {formatCompact(row.censusLifted)} children
        </Text>
      )}
      <Text size="sm" mt={4}>
        Total spending: ${row.totalBenefitB.toFixed(0)}B
      </Text>
      {row.totalBenefitB > 0 && (
        <Text size="sm">
          Cost per person lifted: $
          {Math.round((row.totalBenefitB * 1e9) / row.lifted).toLocaleString()}
        </Text>
      )}
      <Text size="sm" c="dimmed" mt={4}>
        Poverty rate: {(row.rateWithout * 100).toFixed(1)}% &rarr;{" "}
        {(row.rateWith * 100).toFixed(1)}%
      </Text>
    </Box>
  );
}

export function ProgramEffectsChart({
  programs,
  populationView,
}: ProgramEffectsChartProps) {
  const data = buildChartData(programs, populationView);
  const combined = programs.find((p) => p.program === "refundable_credits");

  const populationLabel =
    populationView === "children" ? "child" : "all-person";
  const liftedLabel =
    populationView === "children" ? "Children" : "Persons";

  return (
    <Box>
      <Title order={2} mb="xs">
        Program effects on {populationLabel} poverty
      </Title>
      <Text size="md" c="dimmed" mb="lg" maw={720}>
        {liftedLabel} lifted out of SPM poverty by each program.
        {populationView === "children" &&
          " For programs with Census benchmarks, the comparison shows how PolicyEngine's estimates differ."}
        {" "}PE bars reflect PE-computed benefits on the enhanced CPS.
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
            dataKey="lifted"
            name="PE estimate"
            fill={PE_COLORS.teal500}
            radius={[0, 4, 4, 0]}
          />
          {populationView === "children" && (
            <Bar
              dataKey="censusLifted"
              name="Census estimate"
              fill={PE_COLORS.gray500}
              radius={[0, 4, 4, 0]}
            />
          )}
        </BarChart>
      </ResponsiveContainer>

      {combined && populationView === "children" && (
        <Text size="sm" c="dimmed" mt="xs" ta="center">
          Combined EITC + refundable CTC: PE lifts{" "}
          {formatCompact(combined.children_lifted)} children
          {combined.census_children_lifted_M != null &&
            ` vs Census ${combined.census_children_lifted_M}M`}
        </Text>
      )}
      {combined && populationView === "all_persons" && (
        <Text size="sm" c="dimmed" mt="xs" ta="center">
          Combined EITC + refundable CTC: PE lifts{" "}
          {formatCompact(combined.total_lifted)} persons out of poverty
        </Text>
      )}
    </Box>
  );
}
