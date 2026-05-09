import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { SummaryTable } from "../components/SummaryTable";
import { renderWithProviders } from "./renderWithProviders";
import { TEST_DATA } from "./testData";

describe("SummaryTable", () => {
  it("renders without crashing", () => {
    renderWithProviders(
      <SummaryTable waterfall={TEST_DATA.waterfall} />,
    );
  });

  it("shows all waterfall step labels", () => {
    renderWithProviders(
      <SummaryTable waterfall={TEST_DATA.waterfall} />,
    );
    for (const step of TEST_DATA.waterfall.steps) {
      expect(screen.getByText(step.label)).toBeInTheDocument();
    }
  });

  it("shows poverty rates as percentages", () => {
    renderWithProviders(
      <SummaryTable waterfall={TEST_DATA.waterfall} />,
    );
    // First step: 13.4%
    expect(screen.getByText("13.4%")).toBeInTheDocument();
    // Last step: 22.6%
    expect(screen.getByText("22.6%")).toBeInTheDocument();
  });

  it("shows delta explanations", () => {
    renderWithProviders(
      <SummaryTable waterfall={TEST_DATA.waterfall} />,
    );
    for (const delta of TEST_DATA.waterfall.deltas) {
      expect(screen.getByText(delta.explanation)).toBeInTheDocument();
    }
  });

  it("displays column headers", () => {
    renderWithProviders(
      <SummaryTable waterfall={TEST_DATA.waterfall} />,
    );
    expect(screen.getByText("Step")).toBeInTheDocument();
    expect(screen.getByText("Poverty rate")).toBeInTheDocument();
    expect(screen.getByText("Change")).toBeInTheDocument();
    expect(screen.getByText("Explanation")).toBeInTheDocument();
  });
});
