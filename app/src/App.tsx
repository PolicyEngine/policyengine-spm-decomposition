import {
  Container,
  Text,
  Loader,
  Alert,
  Stack,
  Divider,
  Box,
} from "@mantine/core";
import { useDecompositionData } from "./hooks/useDecompositionData";
import { HeroSection } from "./components/HeroSection";
import { WaterfallChart } from "./components/WaterfallChart";
import { ProgramEffectsChart } from "./components/ProgramEffectsChart";
import { DemographicChart } from "./components/DemographicChart";
import { WeightRebalancingChart } from "./components/WeightRebalancingChart";
import { TaxGapChart } from "./components/TaxGapChart";
import { StatePovertyChart } from "./components/StatePovertyChart";
import { SummaryTable } from "./components/SummaryTable";
import { MethodologySection } from "./components/MethodologySection";
import { PE_COLORS } from "./theme";

export default function App() {
  const { data, loading, error } = useDecompositionData();

  if (loading) {
    return (
      <Container size="lg" py="xl" style={{ textAlign: "center" }}>
        <Loader size="xl" color="teal" />
        <Text mt="md" c="dimmed">
          Loading decomposition data...
        </Text>
      </Container>
    );
  }

  if (error) {
    return (
      <Container size="lg" py="xl">
        <Alert color="red" title="Error loading data">
          {error}
        </Alert>
      </Container>
    );
  }

  if (!data) return null;

  // Check if the raw JSON has the _WARNING field
  const hasWarning = "__WARNING" in data || "_WARNING" in (data as unknown as Record<string, unknown>);

  return (
    <Box
      style={{
        minHeight: "100vh",
        backgroundColor: PE_COLORS.white,
      }}
    >
      <Container size="lg" py="xl">
        <Stack gap="xl">
          <HeroSection data={data} hasWarning={hasWarning} />

          <Divider />

          <WaterfallChart waterfall={data.waterfall} />

          <Divider />

          {data.program_effects && data.program_effects.length > 0 && (
            <>
              <ProgramEffectsChart programs={data.program_effects} />
              <Divider />
            </>
          )}

          {data.demographics && (
            <>
              <DemographicChart demographics={data.demographics} />
              <Divider />
            </>
          )}

          <SummaryTable waterfall={data.waterfall} />

          <Divider />

          <WeightRebalancingChart
            groups={data.weight_rebalancing.groups}
          />

          <Divider />

          <TaxGapChart deciles={data.tax_gap_by_decile} />

          <Divider />

          <StatePovertyChart states={data.state_results} />

          <Divider />

          <MethodologySection metadata={data.metadata} />

          <Box py="md" style={{ textAlign: "center" }}>
            <Text size="xs" c="dimmed">
              Built with PolicyEngine US v{data.metadata.policyengine_us_version}
              {" | "}
              Data generated{" "}
              {new Date(data.metadata.generated_at).toLocaleDateString()}
            </Text>
          </Box>
        </Stack>
      </Container>
    </Box>
  );
}
