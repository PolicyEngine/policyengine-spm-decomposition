import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { MethodologySection } from "../components/MethodologySection";
import { renderWithProviders } from "./renderWithProviders";
import { TEST_DATA } from "./testData";

describe("MethodologySection", () => {
  it("renders without crashing", () => {
    renderWithProviders(
      <MethodologySection metadata={TEST_DATA.metadata} />,
    );
  });

  it("displays a methodology heading", () => {
    renderWithProviders(
      <MethodologySection metadata={TEST_DATA.metadata} />,
    );
    expect(
      screen.getByRole("heading", { name: /^Methodology$/i }),
    ).toBeInTheDocument();
  });

  it("mentions the CPS data", () => {
    renderWithProviders(
      <MethodologySection metadata={TEST_DATA.metadata} />,
    );
    expect(
      screen.getByText(/Current Population Survey/i),
    ).toBeInTheDocument();
  });

  it("mentions PolicyEngine tax modeling", () => {
    renderWithProviders(
      <MethodologySection metadata={TEST_DATA.metadata} />,
    );
    expect(
      screen.getByRole("heading", { name: /tax and benefit modeling/i }),
    ).toBeInTheDocument();
  });

  it("shows the PolicyEngine US version", () => {
    renderWithProviders(
      <MethodologySection metadata={TEST_DATA.metadata} />,
    );
    expect(
      screen.getByText(/1\.534\.5/),
    ).toBeInTheDocument();
  });

  it("includes links to PolicyEngine documentation", () => {
    renderWithProviders(
      <MethodologySection metadata={TEST_DATA.metadata} />,
    );
    const links = screen.getAllByRole("link", { name: /policyengine/i });
    expect(links.length).toBeGreaterThanOrEqual(1);
    expect(links[0]).toHaveAttribute(
      "href",
      expect.stringContaining("policyengine"),
    );
  });
});
