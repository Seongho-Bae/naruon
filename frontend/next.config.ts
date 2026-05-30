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
// etc.) the platform injects the backend's reachable URL via BACKEND_INTERNAL_URL.
//
// Security: an unvalidated BACKEND_INTERNAL_URL would let any operator with
// env-var control redirect /api/* through Next.js to an arbitrary host —
// including cloud metadata endpoints (169.254.169.254) and private RFC 1918
// ranges. Strix flagged this as SSRF. We enforce HTTPS and a hostname denylist
// for any *explicit* value while still allowing the documented loopback
// fallback when the variable is unset (the intended local dev path).
// Patterns are matched against the normalized hostname (lowercased, IPv6
// brackets stripped). Cover IPv4 loopback/private and IPv6 loopback/ULA/
// link-local ranges, plus the cloud metadata link-local /16.
const DENIED_BACKEND_HOST_PATTERNS: readonly RegExp[] = [
  /^localhost$/,
  /^127\./, // IPv4 loopback
  /^0\./, // IPv4 unspecified
  /^10\./, // RFC 1918
  /^192\.168\./, // RFC 1918
  /^172\.(1[6-9]|2\d|3[01])\./, // RFC 1918
  /^169\.254\./, // IPv4 link-local incl. cloud metadata
  /^::1$/, // IPv6 loopback
  /^::$/, // IPv6 unspecified
  /^fc[0-9a-f]{2}:/, // IPv6 unique local (fc00::/7)
  /^fd[0-9a-f]{2}:/,
  /^fe[89ab][0-9a-f]:/, // IPv6 link-local (fe80::/10)
];

function normalizeHost(parsed: URL): string {
  // URL.hostname keeps IPv6 brackets; strip them so a single set of patterns
  // matches both IPv4 and IPv6 literals.
  return parsed.hostname.replace(/^\[/, "").replace(/\]$/, "").toLowerCase();
}

function isAllowedComposeBackendUrl(parsed: URL): boolean {
  return (
    process.env.ALLOW_DOCKER_BACKEND_INTERNAL_URL === "1" &&
    parsed.protocol === "http:" &&
    normalizeHost(parsed) === "backend" &&
    parsed.port === "8000" &&
    (parsed.pathname === "" || parsed.pathname === "/")
  );
}

function assertSafeBackendInternalUrl(raw: string): URL {
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    throw new Error(
      `BACKEND_INTERNAL_URL is not a valid URL: ${JSON.stringify(raw)}`,
    );
  }
  if (isAllowedComposeBackendUrl(parsed)) {
    return parsed;
  }
  if (parsed.protocol !== "https:") {
    throw new Error(
      `BACKEND_INTERNAL_URL must use https:// in split deployments, got ${parsed.protocol}//`,
    );
  }
  const host = normalizeHost(parsed);
  if (!host) {
    throw new Error("BACKEND_INTERNAL_URL must include a hostname");
  }
  for (const pattern of DENIED_BACKEND_HOST_PATTERNS) {
    if (pattern.test(host)) {
      throw new Error(
        `BACKEND_INTERNAL_URL host ${host} is in a private/loopback/link-local range`,
      );
    }
  }
  return parsed;
}

function backendRewriteDestination() {
  const raw = process.env.BACKEND_INTERNAL_URL?.trim();
  // The docker-compose stack uses the in-network service hostname
  // `http://backend:8000`. That exact URL has a separate opt-in via
  // ALLOW_DOCKER_BACKEND_INTERNAL_URL; every other explicit URL must pass
  // the HTTPS + global-host policy.
  if (raw) {
    const parsed = assertSafeBackendInternalUrl(raw);
    const base = `${parsed.origin}${parsed.pathname.replace(/\/+$/, "")}`;
    return `${base}/api/:path*`;
  }
  // No explicit value. The loopback fallback is only safe for local dev
  // and tests where `127.0.0.1` is the same host as the operator's
  // machine. In production builds Strix correctly flagged the
  // unconditional fallback as a residual SSRF vector, so require an
  // explicit BACKEND_INTERNAL_URL there instead.
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "BACKEND_INTERNAL_URL must be set in production builds. " +
        "Set it to the backend's public HTTPS origin (e.g. Render's " +
        "RENDER_EXTERNAL_URL for naruon-backend).",
    );
  }
  return "http://127.0.0.1:8000/api/:path*";
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
