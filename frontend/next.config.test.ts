import { describe, expect, it } from "vitest";

import nextConfig from "./next.config";

async function globalHeaderValue(key: string) {
  const headerRoutes = await nextConfig.headers?.();
  const globalRoute = headerRoutes?.find((route) => route.source === "/(.*)");
  return globalRoute?.headers.find((header) => header.key === key)?.value;
}

describe("next security headers", () => {
  it("allows required app styles without relaxing script policy", async () => {
    const csp = await globalHeaderValue("Content-Security-Policy");

    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("style-src 'self' 'unsafe-inline'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).not.toContain("script-src 'unsafe-inline'");
  });

  it("matches the backend referrer policy", async () => {
    await expect(globalHeaderValue("Referrer-Policy")).resolves.toBe(
      "strict-origin-when-cross-origin",
    );
  });
});
