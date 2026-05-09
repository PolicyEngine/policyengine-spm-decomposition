import { Box, Title, Text, Table } from "@mantine/core";
import type { Waterfall, PopulationView } from "../types/decomposition";
import { PE_COLORS } from "../theme";
import { formatPercent, formatPP } from "../utils/formatters";

interface SummaryTableProps {
  waterfall: Waterfall;
  populationView?: PopulationView;
}

export function SummaryTable({ waterfall, populationView = "children" }: SummaryTableProps) {
  const { steps, deltas } = waterfall;

  const rows = steps.map((step, i) => {
    const delta = i === 0 ? null : deltas[i - 1];
    const isFirst = i === 0;
    const isLast = i === steps.length - 1;

    return (
      <Table.Tr
        key={step.label}
        style={{
          fontWeight: isFirst || isLast ? 600 : 400,
          backgroundColor:
            isFirst || isLast ? PE_COLORS.background : undefined,
        }}
      >
        <Table.Td>{step.label}</Table.Td>
        <Table.Td style={{ fontVariantNumeric: "tabular-nums" }}>
          {formatPercent(step.value)}
        </Table.Td>
        <Table.Td
          style={{
            fontVariantNumeric: "tabular-nums",
            color: delta
              ? delta.delta > 0
                ? PE_COLORS.error
                : PE_COLORS.success
              : undefined,
          }}
        >
          {delta ? formatPP(delta.delta) : "\u2014"}
        </Table.Td>
        <Table.Td>
          {delta?.explanation ?? ""}
        </Table.Td>
      </Table.Tr>
    );
  });

  return (
    <Box>
      <Title order={2} mb="xs">
        {populationView === "children" ? "Child" : "All-person"} poverty decomposition summary
      </Title>
      <Text size="md" c="dimmed" mb="lg" maw={720}>
        Each step from the Census published{" "}
        {populationView === "children" ? "child" : "all-person"} poverty rate
        to PolicyEngine's final estimate, with the percentage point change and
        explanation for each transition.
      </Text>

      <Table
        striped
        highlightOnHover
        withTableBorder
        withColumnBorders
        styles={{
          th: {
            fontFamily: "'Inter', sans-serif",
            fontSize: 13,
            fontWeight: 600,
            color: PE_COLORS.gray700,
          },
          td: {
            fontFamily: "'Inter', sans-serif",
            fontSize: 14,
          },
        }}
      >
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Step</Table.Th>
            <Table.Th>Poverty rate</Table.Th>
            <Table.Th>Change</Table.Th>
            <Table.Th>Explanation</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>{rows}</Table.Tbody>
      </Table>
    </Box>
  );
}
