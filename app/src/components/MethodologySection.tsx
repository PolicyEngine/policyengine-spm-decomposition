import { Box, Title, Text, Anchor, List, Paper } from "@mantine/core";
import type { DecompositionMetadata } from "../types/decomposition";
import { PE_COLORS } from "../theme";

interface MethodologySectionProps {
  metadata: DecompositionMetadata;
}

export function MethodologySection({ metadata }: MethodologySectionProps) {
  return (
    <Box>
      <Title order={2} mb="xs">
        Methodology
      </Title>
      <Text size="md" c="dimmed" mb="lg" maw={720}>
        This analysis decomposes the gap between the Census Bureau's
        published SPM child poverty rate and PolicyEngine's estimate into
        four components.
      </Text>

      <Paper
        p="lg"
        radius="md"
        style={{
          backgroundColor: PE_COLORS.background,
          border: `1px solid ${PE_COLORS.gray300}`,
        }}
      >
        <Title order={3} mb="sm" size="h4">
          Data sources
        </Title>
        <Text size="sm" mb="md">
          The starting point is the Annual Social and Economic Supplement
          (ASEC) of the Current Population Survey (CPS), which is the
          primary data source for official US poverty statistics. We use
          both the raw public-use CPS microdata and an enhanced version
          that recalibrates household weights to match IRS Statistics of
          Income (SOI) aggregate targets.
        </Text>

        <Title order={3} mb="sm" size="h4">
          Tax and benefit modeling
        </Title>
        <Text size="sm" mb="md">
          PolicyEngine computes federal and state taxes, tax credits (such
          as CTC, EITC, and SNAP), and other transfers from scratch using
          its microsimulation engine, rather than relying on the
          self-reported values in the CPS. This bottom-up approach can
          produce different net income figures -- and therefore different
          poverty rates -- than those derived from CPS-reported amounts.
        </Text>

        <Title order={3} mb="sm" size="h4">
          Weight recalibration
        </Title>
        <Text size="sm" mb="md">
          The enhanced CPS adjusts household weights so that aggregate
          income distributions better match IRS SOI data. This tends to
          up-weight lower-income households with children relative to the
          raw CPS, which increases the estimated poverty rate.
        </Text>

        <Title order={3} mb="sm" size="h4">
          Technical details
        </Title>
        <List size="sm" spacing={4}>
          <List.Item>
            PolicyEngine US version: {metadata.policyengine_us_version}
          </List.Item>
          <List.Item>
            Raw CPS dataset: {metadata.raw_cps_dataset}
          </List.Item>
          <List.Item>
            Enhanced CPS dataset: {metadata.enhanced_cps_dataset}
          </List.Item>
          <List.Item>
            Generated: {new Date(metadata.generated_at).toLocaleDateString()}
          </List.Item>
        </List>
      </Paper>

      <Text size="sm" c="dimmed" mt="lg">
        For more details, see the{" "}
        <Anchor
          href="https://policyengine.org/us/research"
          target="_blank"
          rel="noopener noreferrer"
        >
          PolicyEngine research page
        </Anchor>{" "}
        and the{" "}
        <Anchor
          href="https://github.com/PolicyEngine/policyengine-us"
          target="_blank"
          rel="noopener noreferrer"
        >
          PolicyEngine US GitHub repository
        </Anchor>
        .
      </Text>
    </Box>
  );
}
