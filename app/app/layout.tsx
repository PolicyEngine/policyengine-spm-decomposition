import type { Metadata, Viewport } from 'next';
import { MantineProvider, ColorSchemeScript } from '@mantine/core';
import { theme } from './theme';
import './globals.css';

const TITLE = 'SPM poverty rate decomposition — PolicyEngine';
const DESCRIPTION =
  'Decomposition of the change in PolicyEngine SPM poverty rate estimates across versions of the model.';

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  icons: {
    icon: '/assets/logos/policyengine/teal-square.png',
  },
};

export const viewport: Viewport = {
  themeColor: '#2C6496',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider theme={theme}>{children}</MantineProvider>
      </body>
    </html>
  );
}
