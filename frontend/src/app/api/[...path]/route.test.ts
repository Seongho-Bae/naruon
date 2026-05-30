import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { POST } from "./route";

const ORIGINAL_ENV = { ...process.env };

describe("/api runtime proxy route", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    process.env = { ...ORIGINAL_ENV };
    vi.stubEnv("BACKEND_INTERNAL_URL", "https://api.naruon.net");
  });

  afterEach(() => {
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
          Authorization: "Bearer signed-session-token",
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
});
