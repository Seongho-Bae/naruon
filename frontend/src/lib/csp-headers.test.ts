import { describe, expect, it } from "vitest";

import nextConfig, { frontendCspHeaderValue } from "../../next.config";

describe("frontend CSP headers", () => {
  it("allows Next hydration and React inline styles without unsafe eval", async () => {
    expect(nextConfig.headers).toBeDefined();

    const headers = await nextConfig.headers?.();
    const cspHeader = headers
      ?.flatMap((entry) => entry.headers)
      .find((header) => header.key === "Content-Security-Policy");

    expect(cspHeader?.value).toContain("default-src 'self'");
    expect(cspHeader?.value).toContain("script-src 'self' 'unsafe-inline'");
    expect(cspHeader?.value).toContain("style-src 'self' 'unsafe-inline'");
    expect(cspHeader?.value).not.toContain("'unsafe-eval'");
  });

  it("limits unsafe eval to the Next development runtime", () => {
    expect(frontendCspHeaderValue("production")).not.toContain("'unsafe-eval'");
    expect(frontendCspHeaderValue("development")).toContain(
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    );
    expect(frontendCspHeaderValue("development")).toContain(
      "connect-src 'self' http://127.0.0.1:* http://localhost:* ws://127.0.0.1:* ws://localhost:*",
    );
  });
});
