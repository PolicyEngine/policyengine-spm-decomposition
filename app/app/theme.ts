import { createTheme } from "@mantine/core";

export const theme = createTheme({
  fontFamily: "'Inter', sans-serif",
  primaryColor: "teal",
  colors: {
    teal: [
      "#e6fffa",
      "#b2f5ea",
      "#81e6d9",
      "#4fd1c5",
      "#38b2ac",
      "#319795",
      "#2c7a7b",
      "#285e61",
      "#234e52",
      "#1d4044",
    ],
  },
  headings: {
    fontFamily: "'Inter', sans-serif",
  },
});

// PolicyEngine design tokens
export const PE_COLORS = {
  teal500: "#319795",
  teal300: "#4FD1C5",
  gray700: "#344054",
  gray500: "#667085",
  gray300: "#D0D5DD",
  success: "#22C55E",
  error: "#EF4444",
  warning: "#F59E0B",
  white: "#FFFFFF",
  background: "#F9FAFB",
} as const;
