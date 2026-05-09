import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { HeroSection } from "../components/HeroSection";
import { renderWithProviders } from "./renderWithProviders";
import { TEST_DATA } from "./testData";

describe("HeroSection", () => {
  it("renders without crashing", () => {
    renderWithProviders(
      <HeroSection data={TEST_DATA} populationView="children" />,
    );
  });

  it("displays the PolicyEngine poverty estimate", () => {
    renderWithProviders(
      <HeroSection data={TEST_DATA} populationView="children" />,
    );
    expect(screen.getByText(/22\.6%/)).toBeInTheDocument();
  });

  it("displays the Census poverty estimate", () => {
    renderWithProviders(
      <HeroSection data={TEST_DATA} populationView="children" />,
    );
    expect(screen.getByText(/13\.4%/)).toBeInTheDocument();
  });

  it("shows the gap between the two estimates", () => {
    renderWithProviders(
      <HeroSection data={TEST_DATA} populationView="children" />,
    );
    // 22.6 - 13.4 = 9.2 pp gap
    expect(screen.getByText(/9\.2/)).toBeInTheDocument();
  });

  it("shows PE logo", () => {
    renderWithProviders(
      <HeroSection data={TEST_DATA} populationView="children" />,
    );
    const logo = screen.getByAltText("PolicyEngine");
    expect(logo).toBeInTheDocument();
  });

  it("shows sample data banner when _WARNING exists", () => {
    renderWithProviders(
      <HeroSection
        data={TEST_DATA}
        hasWarning={true}
        populationView="children"
      />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getAllByText(/sample data/i).length).toBeGreaterThan(0);
  });

  it("does not show sample data banner when no _WARNING", () => {
    renderWithProviders(
      <HeroSection
        data={TEST_DATA}
        hasWarning={false}
        populationView="children"
      />,
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows all-person poverty rates when populationView is all_persons", () => {
    renderWithProviders(
      <HeroSection data={TEST_DATA} populationView="all_persons" />,
    );
    // All-person Census: 11.6%, PE: 20.3%
    expect(screen.getByText(/11\.6%/)).toBeInTheDocument();
    expect(screen.getByText(/20\.3%/)).toBeInTheDocument();
  });
});
