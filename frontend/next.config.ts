import type { NextConfig } from "next";

function positiveIntegerFromEnv(name: string, fallback: number) {
  const rawValue = process.env[name];
  if (!rawValue) return fallback;
  const parsed = Number.parseInt(rawValue, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

// Backend origin for the same-origin `/api/*` rewrite. In local dev and Docker
// Compose the frontend and backend run on the same host, so the loopback URL
// is the correct fallback. In split deployments (Render Blueprint, Kubernetes,
// etc.) the platform injects the backend's reachable URL via this variable.
function backendRewriteDestination() {
  const raw = process.env.BACKEND_INTERNAL_URL?.trim();
  const base = raw && raw.length > 0 ? raw.replace(/\/+$/, "") : "http://127.0.0.1:8000";
  return `${base}/api/:path*`;
}

const nextConfig: NextConfig = {
  allowedDevOrigins: ['127.0.0.1', 'localhost', '169.254.23.164'],
  devIndicators: false,
  turbopack: {
    root: __dirname,
  },
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
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: backendRewriteDestination(),
      },
    ];
  },
};

export default nextConfig;
