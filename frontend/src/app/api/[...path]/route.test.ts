import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { OPTIONS, POST } from "./route";

const ORIGINAL_ENV = { ...process.env };
const SIGNED_SESSION_TOKEN = "signed-session-token";

describe("/api runtime proxy route", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    process.env = { ...ORIGINAL_ENV };
    vi.stubEnv("BACKEND_INTERNAL_URL", "https://api.naruon.net");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    process.env = { ...ORIGINAL_ENV };
  });

  it("proxies signed requests without forwarding public identity headers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: URL | RequestInfo, init?: RequestInit) => {
        const headers = init?.headers as Headers;
        return Response.json({
          target_url: String(input),
          auth_header: headers.get("authorization"),
          user_header: headers.get("x-user-id"),
          request_body: await new Response(init?.body).text(),
        });
      }),
    );

    const request = new NextRequest(
      "https://frontend.naruon.net/api/tasks?limit=1",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${SIGNED_SESSION_TOKEN}`,
          "Content-Type": "application/json",
          "X-User-Id": "public-user-id",
        },
        body: JSON.stringify({ state: "open" }),
      },
    );

    const response = await POST(request, {
      params: Promise.resolve({ path: ["tasks"] }),
    });

    await expect(response.json()).resolves.toEqual({
      target_url: "https://api.naruon.net/api/tasks?limit=1",
      auth_header: "Bearer signed-session-token",
      user_header: null,
      request_body: '{"state":"open"}',
    });
  });

  it("rejects unsupported query parameters before proxying", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const request = new NextRequest(
      "https://frontend.naruon.net/api/tasks?filename=../../../../etc/passwd",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${SIGNED_SESSION_TOKEN}`,
        },
        body: "{}",
      },
    );

    const response = await POST(request, {
      params: Promise.resolve({ path: ["tasks"] }),
    });

    expect(response.status).toBe(400);
    expect(response.headers.get("referrer-policy")).toBe("no-referrer");
    await expect(response.json()).resolves.toEqual({
      error_code: "invalid_proxy_query",
      message: "Unsupported query parameter: filename",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("re-encodes allowed query parameters instead of copying the raw search string", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: URL | RequestInfo) =>
        Response.json({ target_url: String(input) }),
      ),
    );

    const request = new NextRequest(
      "https://frontend.naruon.net/api/ontology/relationships?source_message_id=%3Cabc@example.com%3E&source_thread_id=thread/one",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${SIGNED_SESSION_TOKEN}`,
        },
        body: "{}",
      },
    );

    const response = await POST(request, {
      params: Promise.resolve({ path: ["ontology", "relationships"] }),
    });

    await expect(response.json()).resolves.toEqual({
      target_url:
        "https://api.naruon.net/api/ontology/relationships?source_message_id=%3Cabc%40example.com%3E&source_thread_id=thread%2Fone",
    });
  });

  it("rejects unsigned unsafe requests before proxying", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const consoleWarnMock = vi.spyOn(console, "warn").mockImplementation(vi.fn());

    const request = new NextRequest(
      "https://frontend.naruon.net/api/login",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "credential=placeholder",
      },
    );

    const response = await POST(request, {
      params: Promise.resolve({ path: ["login"] }),
    });

    expect(response.status).toBe(401);
    expect(response.headers.get("referrer-policy")).toBe("no-referrer");
    await expect(response.json()).resolves.toEqual({
      error_code: "missing_bearer_session",
      message: "Authentication required",
    });
    expect(fetchMock).not.toHaveBeenCalled();
    expect(consoleWarnMock).toHaveBeenCalledWith(
      "Rejected unsigned unsafe API proxy request",
      {
        method: "POST",
        route: "/api/[...path]",
      },
    );
  });

  it("allows unsigned OPTIONS preflight requests to reach the backend proxy", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: URL | RequestInfo, init?: RequestInit) =>
        Response.json({
          target_url: String(input),
          method: init?.method,
        }),
      ),
    );

    const request = new NextRequest("https://frontend.naruon.net/api/tasks", {
      method: "OPTIONS",
    });

    const response = await OPTIONS(request, {
      params: Promise.resolve({ path: ["tasks"] }),
    });

    await expect(response.json()).resolves.toEqual({
      target_url: "https://api.naruon.net/api/tasks",
      method: "OPTIONS",
    });
  });
});
