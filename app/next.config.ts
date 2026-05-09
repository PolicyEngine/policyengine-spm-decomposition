import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Mantine ships CJS interop and relies on browser globals; transpiling via
  // Next avoids ESM/CJS mismatch errors during build. Recharts is also added
  // for safety since it depends on browser-only APIs.
  transpilePackages: ['@mantine/core', '@mantine/hooks', 'recharts'],
  // Pin the workspace root so Turbopack does not silently pick up a stray
  // lockfile from a parent directory during local development or CI.
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
