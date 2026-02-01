import { render, type RenderOptions } from "@testing-library/react";
import { MantineProvider } from "@mantine/core";
import { theme } from "../theme";
import type { ReactElement } from "react";

export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) {
  return render(ui, {
    wrapper: ({ children }) => (
      <MantineProvider theme={theme}>{children}</MantineProvider>
    ),
    ...options,
  });
}
