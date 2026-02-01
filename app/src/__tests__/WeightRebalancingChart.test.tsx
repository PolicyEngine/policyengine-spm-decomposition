import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { WeightRebalancingChart } from "../components/WeightRebalancingChart";
import { renderWithProviders } from "./renderWithProviders";
import { TEST_DATA } from "./testData";

describe("WeightRebalancingChart", () => {
  it("renders without crashing", () => {
    renderWithProviders(
      <WeightRebalancingChart
        groups={TEST_DATA.weight_rebalancing.groups}
      />,
    );
  });

  it("displays a section title", () => {
    renderWithProviders(
      <WeightRebalancingChart
        groups={TEST_DATA.weight_rebalancing.groups}
      />,
    );
    expect(
      screen.getByRole("heading", { name: /weight rebalancing/i }),
    ).toBeInTheDocument();
  });

  it("displays an explanation paragraph about poverty rates", () => {
    renderWithProviders(
      <WeightRebalancingChart
        groups={TEST_DATA.weight_rebalancing.groups}
      />,
    );
    expect(
      screen.getByText(/Comparing the SPM child poverty rate/i),
    ).toBeInTheDocument();
  });
});
