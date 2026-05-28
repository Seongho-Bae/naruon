import type { NextConfig } from "next";

function positiveIntegerFromEnv(name: string, fallback: number) {
  const rawValue = process.env[name];
  if (!rawValue) return fallback;
  const parsed = Number.parseInt(rawValue, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

const nextConfig: NextConfig = {
  allowedDevOrigins: ['127.0.0.1', 'localhost', '169.254.23.164'],
  devIndicators: false,
  turbopack: {
    root: __dirname,
  },
  experimental: {
    cpus: positiveIntegerFromEnv("NEXT_BUILD_CPUS", 2),
    staticGenerationMaxConcurrency: positiveIntegerFromEnv(
      "NEXT_STATIC_GENERATION_MAX_CONCURRENCY",
      2,
    ),
    staticGenerationMinPagesPerWorker: positiveIntegerFromEnv(
      "NEXT_STATIC_GENERATION_MIN_PAGES_PER_WORKER",
      50,
    ),
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
