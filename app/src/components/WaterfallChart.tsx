import { Box, Title, Text } from "@mantine/core";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { DecompositionData } from "../types/decomposition";
import { PE_COLORS } from "../theme";
import { CHART_MARGIN, CHART_COLORS, CHART_FONT } from "../utils/chartConfig";
import { formatPercent, formatPP } from "../utils/formatters";

interface WaterfallChartProps {
  waterfall: DecompositionData["waterfall"];
}

interface WaterfallBarData {
  label: string;
  shortLabel: string;
  base: number;
  value: number;
  delta: number;
  explanation: string;
  isEndpoint: boolean;
}

function buildWaterfallData(
  waterfall: DecompositionData["waterfall"],
): WaterfallBarData[] {
  const { steps, deltas } = waterfall;
  const items: WaterfallBarData[] = [];

  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const isFirst = i === 0;
    const isLast = i === steps.length - 1;
    const isEndpoint = isFirst || isLast;

    // For endpoints, show the full bar from 0
    // For intermediates, show the delta bar
    const delta = isFirst ? 0 : deltas[i - 1]?.delta ?? 0;
    const base = isEndpoint ? 0 : steps[i - 1].value;
    const value = isEndpoint ? step.value : delta;

    // Create a short label for the x-axis
    const shortLabel = step.label
      .replace(" (2024)", "")
      .replace("Census published", "Census")
      .replace("Raw CPS reported", "Raw CPS\nreported")
      .replace("Raw CPS PE-computed", "Raw CPS\nPE-computed")
      .replace("Enhanced CPS reported", "Enhanced CPS\nreported")
      .replace("Enhanced CPS PE-computed", "Enhanced CPS\nPE-computed");

    items.push({
      label: step.label,
      shortLabel,
      base,
      value,
      delta,
      explanation: isFirst
        ? "Starting point"
        : deltas[i - 1]?.explanation ?? "",
      isEndpoint,
    });
  }

  return items;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: WaterfallBarData }>;
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
        maxWidth: 280,
      }}
    >
      <Text fw={600} size="sm">
        {d.label}
      </Text>
      <Text size="sm" mt={4}>
        Poverty rate: {formatPercent(d.base + d.value)}
      </Text>
      {!d.isEndpoint && (
        <Text size="sm" c="dimmed" mt={4}>
          {formatPP(d.delta)}: {d.explanation}
        </Text>
      )}
    </Box>
  );
}

export function WaterfallChart({ waterfall }: WaterfallChartProps) {
  const data = buildWaterfallData(waterfall);

  return (
    <Box>
      <Title order={2} mb="xs">
        Waterfall decomposition
      </Title>
      <Text size="md" c="dimmed" mb="lg" maw={720}>
        Each step shows how the SPM child poverty rate changes from the
        Census published figure to PolicyEngine's final estimate. Bars in
        red indicate increases in the poverty rate; green bars indicate
        decreases.
      </Text>

      <ResponsiveContainer width="100%" height={420}>
        <BarChart
          data={data}
          margin={{ ...CHART_MARGIN, bottom: 80 }}
        >
          <XAxis
            dataKey="shortLabel"
            tick={{ ...CHART_FONT, fontSize: 11 }}
            interval={0}
            angle={0}
            height={80}
          />
          <YAxis
            tickFormatter={(v: number) => formatPercent(v)}
            tick={CHART_FONT}
            domain={[0, "auto"]}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke={PE_COLORS.gray300} />

          {/* Invisible base bar */}
          <Bar dataKey="base" stackId="stack" fill="transparent" />

          {/* Visible value bar */}
          <Bar dataKey="value" stackId="stack" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => {
              let fill: string;
              if (entry.isEndpoint) {
                fill = CHART_COLORS.primary;
              } else if (entry.delta > 0) {
                fill = CHART_COLORS.negative;
              } else {
                fill = CHART_COLORS.positive;
              }
              return <Cell key={i} fill={fill} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}
