import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { HeroSection } from "../components/HeroSection";
import { renderWithProviders } from "./renderWithProviders";
import { TEST_DATA, TEST_DATA_WITH_WARNING } from "./testData";

describe("HeroSection", () => {
  it("renders without crashing", () => {
    renderWithProviders(<HeroSection data={TEST_DATA} />);
  });

  it("displays the PolicyEngine poverty estimate", () => {
    renderWithProviders(<HeroSection data={TEST_DATA} />);
    expect(screen.getByText(/22\.6%/)).toBeInTheDocument();
  });

  it("displays the Census poverty estimate", () => {
    renderWithProviders(<HeroSection data={TEST_DATA} />);
    expect(screen.getByText(/13\.4%/)).toBeInTheDocument();
  });

  it("shows the gap between the two estimates", () => {
    renderWithProviders(<HeroSection data={TEST_DATA} />);
    // 22.6 - 13.4 = 9.2 pp gap
    expect(screen.getByText(/9\.2/)).toBeInTheDocument();
  });

  it("shows PE logo", () => {
    renderWithProviders(<HeroSection data={TEST_DATA} />);
    const logo = screen.getByAltText("PolicyEngine");
    expect(logo).toBeInTheDocument();
  });

  it("shows sample data banner when _WARNING exists", () => {
    renderWithProviders(
      <HeroSection data={TEST_DATA} hasWarning={true} />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getAllByText(/sample data/i).length).toBeGreaterThan(0);
  });

  it("does not show sample data banner when no _WARNING", () => {
    renderWithProviders(
      <HeroSection data={TEST_DATA} hasWarning={false} />,
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
