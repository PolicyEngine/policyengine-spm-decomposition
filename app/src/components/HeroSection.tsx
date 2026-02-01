import {
  Box,
  Title,
  Text,
  Group,
  Image,
  Alert,
  Paper,
} from "@mantine/core";
import type { DecompositionData } from "../types/decomposition";
import { PE_COLORS } from "../theme";
import { LOGO_URL } from "../utils/chartConfig";

interface HeroSectionProps {
  data: DecompositionData;
  hasWarning?: boolean;
}

export function HeroSection({ data, hasWarning = false }: HeroSectionProps) {
  const censusRate = data.waterfall.steps[0]?.value ?? 0;
  const peRate = data.waterfall.steps.at(-1)?.value ?? 0;
  const gap = peRate - censusRate;

  return (
    <Box>
      {hasWarning && (
        <Alert
          color="yellow"
          mb="md"
          title="Sample data"
          styles={{ root: { fontSize: 14 } }}
        >
          This page is showing sample data. Values are approximations and
          will be replaced by the Python pipeline output.
        </Alert>
      )}

      <Group justify="space-between" align="flex-start" mb="xl">
        <Box style={{ flex: 1 }}>
          <Title
            order={1}
            style={{
              fontSize: "2.25rem",
              lineHeight: 1.2,
              color: PE_COLORS.gray700,
            }}
          >
            SPM child poverty rate decomposition
          </Title>
          <Text size="lg" c="dimmed" mt="sm" maw={720}>
            Understanding why PolicyEngine and the Census Bureau report
            different Supplemental Poverty Measure (SPM) child poverty rates
          </Text>
        </Box>
        <Image
          src={LOGO_URL}
          alt="PolicyEngine"
          w={160}
          fit="contain"
          style={{ flexShrink: 0 }}
        />
      </Group>

      <Group gap="lg" mb="xl" grow>
        <Paper
          p="xl"
          radius="md"
          style={{
            backgroundColor: PE_COLORS.background,
            borderLeft: `4px solid ${PE_COLORS.gray500}`,
          }}
        >
          <Text size="sm" fw={500} c="dimmed" tt="uppercase" mb={4}>
            Census published
          </Text>
          <Text
            fw={700}
            style={{ fontSize: "2.5rem", lineHeight: 1, color: PE_COLORS.gray700 }}
          >
            {(censusRate * 100).toFixed(1)}%
          </Text>
          <Text size="sm" c="dimmed" mt={4}>
            SPM child poverty rate
          </Text>
        </Paper>

        <Paper
          p="xl"
          radius="md"
          style={{
            backgroundColor: PE_COLORS.background,
            borderLeft: `4px solid ${PE_COLORS.teal500}`,
          }}
        >
          <Text size="sm" fw={500} c="dimmed" tt="uppercase" mb={4}>
            PolicyEngine estimate
          </Text>
          <Text
            fw={700}
            style={{ fontSize: "2.5rem", lineHeight: 1, color: PE_COLORS.teal500 }}
          >
            {(peRate * 100).toFixed(1)}%
          </Text>
          <Text size="sm" c="dimmed" mt={4}>
            SPM child poverty rate
          </Text>
        </Paper>

        <Paper
          p="xl"
          radius="md"
          style={{
            backgroundColor: PE_COLORS.background,
            borderLeft: `4px solid ${PE_COLORS.error}`,
          }}
        >
          <Text size="sm" fw={500} c="dimmed" tt="uppercase" mb={4}>
            Gap
          </Text>
          <Text
            fw={700}
            style={{ fontSize: "2.5rem", lineHeight: 1, color: PE_COLORS.error }}
          >
            +{(gap * 100).toFixed(1)} pp
          </Text>
          <Text size="sm" c="dimmed" mt={4}>
            percentage point difference
          </Text>
        </Paper>
      </Group>
    </Box>
  );
}
