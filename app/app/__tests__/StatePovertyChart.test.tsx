import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { StatePovertyChart } from "../components/StatePovertyChart";
import { renderWithProviders } from "./renderWithProviders";
import { TEST_DATA } from "./testData";

describe("StatePovertyChart", () => {
  it("renders without crashing", () => {
    renderWithProviders(
      <StatePovertyChart states={TEST_DATA.state_results} />,
    );
  });

  it("displays a section title", () => {
    renderWithProviders(
      <StatePovertyChart states={TEST_DATA.state_results} />,
    );
    expect(
      screen.getByRole("heading", { name: /state-level poverty/i }),
    ).toBeInTheDocument();
  });

  it("displays an explanation paragraph about the 45-degree line", () => {
    renderWithProviders(
      <StatePovertyChart states={TEST_DATA.state_results} />,
    );
    expect(
      screen.getByText(/States above the line have a higher/i),
    ).toBeInTheDocument();
  });
});
