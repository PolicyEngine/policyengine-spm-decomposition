import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { TaxGapChart } from "../components/TaxGapChart";
import { renderWithProviders } from "./renderWithProviders";
import { TEST_DATA } from "./testData";

describe("TaxGapChart", () => {
  it("renders without crashing", () => {
    renderWithProviders(
      <TaxGapChart deciles={TEST_DATA.tax_gap_by_decile} />,
    );
  });

  it("displays a section title about tax gap", () => {
    renderWithProviders(
      <TaxGapChart deciles={TEST_DATA.tax_gap_by_decile} />,
    );
    expect(
      screen.getByRole("heading", { name: /tax gap/i }),
    ).toBeInTheDocument();
  });

  it("displays an explanation paragraph", () => {
    renderWithProviders(
      <TaxGapChart deciles={TEST_DATA.tax_gap_by_decile} />,
    );
    expect(
      screen.getByText(/Mean federal tax per household/i),
    ).toBeInTheDocument();
  });
});
