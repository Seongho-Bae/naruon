import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { POST } from "./route";

const ORIGINAL_ENV = { ...process.env };

describe("/auth/oidc/login route", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    process.env = { ...ORIGINAL_ENV };
    vi.stubEnv("NEXT_PUBLIC_OIDC_ISSUER_URL", "https://login.example.com/realms/naruon/");
    vi.stubEnv("NEXT_PUBLIC_OIDC_CLIENT_ID", "naruon-web");
    vi.stubEnv("NEXT_PUBLIC_OIDC_REDIRECT_URI", "https://app.example.com/auth/callback");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    process.env = { ...ORIGINAL_ENV };
  });

  it("sets transient OIDC PKCE state in an HttpOnly cookie and returns an authorization URL", async () => {
    const response = await POST(new NextRequest("https://app.example.com/auth/oidc/login", {
      method: "POST",
      body: JSON.stringify({ return_to: "/settings?tab=security#oidc" }),
    }));

    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toBe("no-store");
    const body = await response.json() as { authorization_url: string };
    const authorizationUrl = new URL(body.authorization_url);
    expect(authorizationUrl.origin).toBe("https://login.example.com");
    expect(authorizationUrl.searchParams.get("response_type")).toBe("code");
    expect(authorizationUrl.searchParams.get("client_id")).toBe("naruon-web");
    expect(authorizationUrl.searchParams.get("redirect_uri")).toBe("https://app.example.com/auth/callback");
    expect(authorizationUrl.searchParams.get("code_challenge_method")).toBe("S256");
    expect(authorizationUrl.searchParams.get("state")).toMatch(/^[A-Za-z0-9_-]{32,}$/);
    expect(authorizationUrl.searchParams.get("code_challenge")).toMatch(/^[A-Za-z0-9_-]{32,}$/);

    const setCookie = response.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("naruon_oidc_pkce=");
    expect(setCookie).toContain("HttpOnly");
    expect(setCookie).toContain("Secure");
    expect(setCookie).toContain("SameSite=lax");
    expect(setCookie).toContain("Path=/auth");
    expect(setCookie).not.toContain("code_challenge");
    expect(setCookie).not.toContain("return_to");
  });
});
