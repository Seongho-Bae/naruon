import type { NextConfig } from "next";

const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

function positiveIntegerFromEnv(name: string, fallback: number) {
  const rawValue = process.env[name];
  if (!rawValue) return fallback;
  const parsed = Number.parseInt(rawValue, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

const nextConfig: NextConfig = {
  allowedDevOrigins: ['127.0.0.1', 'localhost', '169.254.23.164'],
  devIndicators: false,
  outputFileTracingRoot: __dirname,
  experimental: {
    // Best-effort local guard only: CI/Docker/runner CPU limits remain authoritative.
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
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: CONTENT_SECURITY_POLICY,
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
