import { useState } from "react";
import {
  Container,
  Text,
  Loader,
  Alert,
  Stack,
  Divider,
  Box,
  SegmentedControl,
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
import type { PopulationView } from "./types/decomposition";

export default function App() {
  const { data, loading, error } = useDecompositionData();
  const [populationView, setPopulationView] =
    useState<PopulationView>("children");

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

  const hasWarning =
    "__WARNING" in data ||
    "_WARNING" in (data as unknown as Record<string, unknown>);

  const hasAllPersons = !!data.all_persons_waterfall;
  const activeWaterfall =
    populationView === "all_persons" && data.all_persons_waterfall
      ? data.all_persons_waterfall
      : data.waterfall;

  return (
    <Box
      style={{
        minHeight: "100vh",
        backgroundColor: PE_COLORS.white,
      }}
    >
      <Container size="lg" py="xl">
        <Stack gap="xl">
          <HeroSection
            data={data}
            hasWarning={hasWarning}
            populationView={populationView}
          />

          {hasAllPersons && (
            <Box>
              <SegmentedControl
                value={populationView}
                onChange={(v) => setPopulationView(v as PopulationView)}
                data={[
                  { label: "Children", value: "children" },
                  { label: "All persons", value: "all_persons" },
                ]}
                color="teal"
                size="md"
              />
            </Box>
          )}

          <Divider />

          <WaterfallChart
            waterfall={activeWaterfall}
            populationLabel={
              populationView === "children" ? "child" : "all-person"
            }
          />

          <Divider />

          {data.program_effects && data.program_effects.length > 0 && (
            <>
              <ProgramEffectsChart
                programs={data.program_effects}
                populationView={populationView}
              />
              <Divider />
            </>
          )}

          {data.demographics && populationView === "children" && (
            <>
              <DemographicChart demographics={data.demographics} />
              <Divider />
            </>
          )}

          <SummaryTable waterfall={activeWaterfall} populationView={populationView} />

          <Divider />

          <WeightRebalancingChart
            groups={data.weight_rebalancing.groups}
          />

          <Divider />

          <TaxGapChart deciles={data.tax_gap_by_decile} />

          <Divider />

          {data.state_results && data.state_results.length > 0 && (
            <>
              <StatePovertyChart states={data.state_results} />
              <Divider />
            </>
          )}

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
