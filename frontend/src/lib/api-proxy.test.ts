import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildBackendUrl,
  buildProxyHeaders,
  pathSegmentsFromProxyPath,
  proxyBackendRequest,
} from "./api-proxy";


describe("API proxy helpers", () => {
  afterEach(() => {
    delete process.env.API_AUTH_TOKEN;
    delete process.env.API_INTERNAL_URL;
    delete process.env.API_PROXY_ALLOW_SHARED_TOKEN;
    vi.unstubAllGlobals();
  });

  it("builds upstream backend URLs from catch-all route segments", () => {
    const url = buildBackendUrl(
      ["api", "network", "graph"],
      "?limit=20",
      "http://backend:8000/",
    );

    expect(url.toString()).toBe("http://backend:8000/api/network/graph?limit=20");
  });

  it("uses server-only bearer tokens and drops spoofed client authorization", () => {
    const headers = buildProxyHeaders(
      new Headers({
        Authorization: "Bearer attacker",
        Cookie: "session=browser-cookie",
        "Content-Type": "application/json",
      }),
      "signed-server-token",
    );

    expect(headers.get("Authorization")).toBe("Bearer signed-server-token");
    expect(headers.has("Cookie")).toBe(false);
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("normalizes query-provided backend paths without allowing traversal", () => {
    expect(pathSegmentsFromProxyPath("/api/emails/thread/thread-b")).toEqual([
      "api",
      "emails",
      "thread",
      "thread-b",
    ]);
    expect(pathSegmentsFromProxyPath(null)).toBeNull();
    expect(pathSegmentsFromProxyPath("../api/emails")).toBeNull();
    expect(pathSegmentsFromProxyPath("/api/../secrets")).toBeNull();
  });

  it("does not expose the shared-token proxy unless local demo mode is explicit", async () => {
    process.env.API_AUTH_TOKEN = "signed-server-token";
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await proxyBackendRequest(
      new Request("http://frontend.local/api/backend/api/emails"),
      ["api", "emails"],
    );

    expect(response.status).toBe(403);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("forwards through the shared-token proxy when local demo mode is explicit", async () => {
    process.env.API_AUTH_TOKEN = "signed-server-token";
    process.env.API_INTERNAL_URL = "http://backend:8000";
    process.env.API_PROXY_ALLOW_SHARED_TOKEN = "true";
    const fetchMock = vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify({ emails: [] }), { status: 200 })),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await proxyBackendRequest(
      new Request("http://frontend.local/api/backend/api/emails?limit=1"),
      ["api", "emails"],
    );

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledWith(
      new URL("http://backend:8000/api/emails?limit=1"),
      expect.objectContaining({
        headers: expect.any(Headers),
        method: "GET",
        redirect: "manual",
      }),
    );
    const headers = fetchMock.mock.calls[0]?.[1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer signed-server-token");
  });
});
