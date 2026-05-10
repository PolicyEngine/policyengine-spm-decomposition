import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { WaterfallChart } from "../components/WaterfallChart";
import { renderWithProviders } from "./renderWithProviders";
import { TEST_DATA } from "./testData";

describe("WaterfallChart", () => {
  it("renders without crashing", () => {
    renderWithProviders(
      <WaterfallChart waterfall={TEST_DATA.waterfall} />,
    );
  });

  it("displays a section title", () => {
    renderWithProviders(
      <WaterfallChart waterfall={TEST_DATA.waterfall} />,
    );
    expect(
      screen.getByRole("heading", { name: /waterfall decomposition/i }),
    ).toBeInTheDocument();
  });

  it("displays an explanation paragraph", () => {
    renderWithProviders(
      <WaterfallChart waterfall={TEST_DATA.waterfall} />,
    );
    expect(
      screen.getByText(/Census published figure to PolicyEngine/i),
    ).toBeInTheDocument();
  });
});
