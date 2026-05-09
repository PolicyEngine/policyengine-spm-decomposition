import { Box, Title, Text } from "@mantine/core";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Label,
} from "recharts";
import type { StateResult } from "../types/decomposition";
import { PE_COLORS } from "../theme";
import { CHART_MARGIN, CHART_COLORS, CHART_FONT } from "../utils/chartConfig";
import { formatPercent } from "../utils/formatters";

interface StatePovertyChartProps {
  states: StateResult[];
}

interface ChartPoint {
  state: string;
  x: number; // reported poverty rate
  y: number; // computed poverty rate
  totalChildren: number;
}

function buildChartData(states: StateResult[]): ChartPoint[] {
  return states.map((s) => ({
    state: s.state,
    x: s.reported_child_poverty,
    y: s.computed_child_poverty,
    totalChildren: s.total_children,
  }));
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartPoint }>;
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;

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
        {d.state}
      </Text>
      <Text size="sm">
        CPS-reported: {formatPercent(d.x)}
      </Text>
      <Text size="sm">
        PE-computed: {formatPercent(d.y)}
      </Text>
      <Text size="sm" c="dimmed" mt={4}>
        {(d.totalChildren / 1e6).toFixed(1)}M children
      </Text>
    </Box>
  );
}

// Custom dot renderer that labels each state
function renderDot(props: unknown) {
  const { cx, cy, payload } = props as {
    cx: number;
    cy: number;
    payload: ChartPoint;
  };
  return (
    <g>
      <circle
        cx={cx}
        cy={cy}
        r={6}
        fill={CHART_COLORS.primary}
        stroke="white"
        strokeWidth={2}
      />
      <text
        x={cx + 10}
        y={cy - 6}
        fill={PE_COLORS.gray700}
        fontSize={11}
        fontFamily="'Inter', sans-serif"
      >
        {payload.state}
      </text>
    </g>
  );
}

export function StatePovertyChart({ states }: StatePovertyChartProps) {
  const data = buildChartData(states);

  // Compute domain -- find min/max across both axes, pad
  const allValues = data.flatMap((d) => [d.x, d.y]);
  const minVal = Math.max(0, Math.min(...allValues) - 0.02);
  const maxVal = Math.min(1, Math.max(...allValues) + 0.04);

  return (
    <Box>
      <Title order={2} mb="xs">
        State-level poverty comparison
      </Title>
      <Text size="md" c="dimmed" mb="lg" maw={720}>
        Each dot is a state. The x-axis shows the CPS-reported child
        poverty rate; the y-axis shows PolicyEngine's computed rate. States
        above the line have a higher PE-computed poverty rate than the CPS
        reports.
      </Text>

      <ResponsiveContainer width="100%" height={480}>
        <ScatterChart margin={{ ...CHART_MARGIN, bottom: 50 }}>
          <XAxis
            type="number"
            dataKey="x"
            name="Reported"
            domain={[minVal, maxVal]}
            tickFormatter={(v: number) => formatPercent(v)}
            tick={CHART_FONT}
          >
            <Label
              value="CPS-reported child poverty"
              position="bottom"
              offset={20}
              style={{ ...CHART_FONT, fill: PE_COLORS.gray700 }}
            />
          </XAxis>
          <YAxis
            type="number"
            dataKey="y"
            name="Computed"
            domain={[minVal, maxVal]}
            tickFormatter={(v: number) => formatPercent(v)}
            tick={CHART_FONT}
          >
            <Label
              value="PE-computed child poverty"
              angle={-90}
              position="left"
              offset={20}
              style={{ ...CHART_FONT, fill: PE_COLORS.gray700 }}
            />
          </YAxis>
          <Tooltip content={<CustomTooltip />} />

          {/* 45-degree reference line (y=x) */}
          <ReferenceLine
            segment={[
              { x: minVal, y: minVal },
              { x: maxVal, y: maxVal },
            ]}
            stroke={PE_COLORS.gray300}
            strokeDasharray="6 3"
            strokeWidth={1.5}
          />

          <Scatter
            data={data}
            fill={CHART_COLORS.primary}
            shape={renderDot}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </Box>
  );
}
