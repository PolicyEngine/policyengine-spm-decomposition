import { Box, Title, Text, SimpleGrid } from "@mantine/core";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { Demographics, DemographicGroup } from "../types/decomposition";
import { PE_COLORS } from "../theme";
import { CHART_MARGIN, CHART_FONT } from "../utils/chartConfig";
import { formatPercent } from "../utils/formatters";

interface DemographicChartProps {
  demographics: Demographics;
}

interface ChartRow {
  group: string;
  peRate: number;
  censusRate: number | null;
  totalChildren: number;
}

function buildChartData(groups: DemographicGroup[]): ChartRow[] {
  return groups.map((g) => ({
    group: g.group,
    peRate: g.pe_rate,
    censusRate: g.census_rate,
    totalChildren: g.total_children,
  }));
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
        maxWidth: 280,
      }}
    >
      <Text fw={600} size="sm" mb={4}>
        {row.group}
      </Text>
      <Text size="sm">PE rate: {formatPercent(row.peRate)}</Text>
      {row.censusRate !== null && (
        <Text size="sm" c="dimmed">
          Census rate: {formatPercent(row.censusRate)}
        </Text>
      )}
      <Text size="sm" mt={4} c="dimmed">
        {(row.totalChildren / 1e6).toFixed(1)}M children
      </Text>
    </Box>
  );
}

function DemographicBarChart({
  title,
  data,
}: {
  title: string;
  data: ChartRow[];
}) {
  return (
    <Box>
      <Text fw={600} size="md" mb="xs">
        {title}
      </Text>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={data}
          margin={{ ...CHART_MARGIN, left: 120, bottom: 20 }}
          layout="vertical"
        >
          <XAxis
            type="number"
            tickFormatter={(v: number) => formatPercent(v)}
            tick={CHART_FONT}
            domain={[0, "auto"]}
          />
          <YAxis
            dataKey="group"
            type="category"
            tick={{ ...CHART_FONT, fontSize: 12 }}
            width={110}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ ...CHART_FONT, paddingTop: 8 }} />
          <Bar
            dataKey="peRate"
            name="PE rate"
            fill={PE_COLORS.teal500}
            radius={[0, 4, 4, 0]}
          />
          <Bar
            dataKey="censusRate"
            name="Census rate"
            fill={PE_COLORS.gray500}
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}

export function DemographicChart({ demographics }: DemographicChartProps) {
  const ageData = buildChartData(demographics.by_age);
  const raceData = buildChartData(demographics.by_race);

  return (
    <Box>
      <Title order={2} mb="xs">
        Demographic breakdowns
      </Title>
      <Text size="md" c="dimmed" mb="lg" maw={720}>
        SPM child poverty rates by demographic group. PE rates reflect
        PolicyEngine's computation on the enhanced CPS; Census rates are
        approximate benchmarks from Census Bureau publications.
      </Text>

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="xl">
        <DemographicBarChart title="By age group" data={ageData} />
        <DemographicBarChart title="By race / ethnicity" data={raceData} />
      </SimpleGrid>
    </Box>
  );
}
