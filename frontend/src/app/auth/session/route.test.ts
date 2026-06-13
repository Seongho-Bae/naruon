import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { DELETE, GET, POST } from "./route";

function base64UrlJson(body: unknown) {
  return Buffer.from(JSON.stringify(body)).toString("base64url");
}

function signedFixtureToken(payload: Record<string, unknown>) {
  return `${base64UrlJson({ alg: "HS256", typ: "JWT" })}.${base64UrlJson(payload)}.signature`;
}

describe("/auth/session route", () => {
  it("stores the bearer token in an HttpOnly secure same-site cookie", async () => {
    const token = signedFixtureToken({
      sub: "user-1",
      org: "org-acme",
      workspace: "workspace-acme",
      exp: Math.floor(Date.now() / 1000) + 300,
    });

    const response = await POST(new NextRequest("https://app.naruon.net/auth/session", {
      method: "POST",
      body: JSON.stringify({ access_token: token }),
    }));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      authenticated: true,
      claims: {
        userId: "user-1",
        organizationId: "org-acme",
        workspaceId: "workspace-acme",
      },
    });
    const setCookie = response.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("naruon_session=");
    expect(setCookie).toContain("HttpOnly");
    expect(setCookie).toContain("Secure");
    expect(setCookie).toContain("SameSite=lax");
    expect(setCookie).not.toContain("access_token");
  });

  it("returns public claims without exposing the cookie value", async () => {
    const token = signedFixtureToken({
      sub: "user-2",
      org: "org-beta",
      workspace: "workspace-beta",
    });
    const request = new NextRequest("https://app.naruon.net/auth/session", {
      headers: { Cookie: `naruon_session=${token}` },
    });

    const response = await GET(request);

    await expect(response.json()).resolves.toEqual({
      authenticated: true,
      claims: {
        userId: "user-2",
        organizationId: "org-beta",
        workspaceId: "workspace-beta",
      },
    });
    expect(response.headers.get("set-cookie")).toBeNull();
  });

  it("expires the session cookie on logout", async () => {
    const response = await DELETE(new NextRequest("https://app.naruon.net/auth/session", {
      method: "DELETE",
    }));

    expect(response.status).toBe(200);
    const setCookie = response.headers.get("set-cookie") ?? "";
    expect(setCookie).toContain("naruon_session=");
    expect(setCookie).toContain("Max-Age=0");
    expect(setCookie).toContain("HttpOnly");
    expect(setCookie).toContain("Secure");
    expect(setCookie).toContain("SameSite=lax");
  });
});
