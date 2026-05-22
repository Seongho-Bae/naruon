/* @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClient } from "./api-client";

function base64UrlJson(body: unknown) {
  return btoa(JSON.stringify(body)).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

function jsonResponse(body: unknown) {
  return {
    ok: true,
    json: async () => body,
  };
}

function mockFetchResponse(body: unknown) {
  return vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    void input;
    void init;
    return Promise.resolve(jsonResponse(body));
  });
}

function seedLegacyStoredSession(token: string) {
  localStorage.setItem(["naruon", "session", "token"].join("_"), token);
}

describe("ApiClient", () => {
  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("does not derive display user context from web storage tokens", () => {
    localStorage.setItem("naruon_dev_user", "legacy-dev-user");
    const client = new ApiClient();

    localStorage.setItem(
      ["naruon", "session", "token"].join("_"),
      `${base64UrlJson({ alg: "HS256" })}.${base64UrlJson({ sub: "signed-user" })}.signature`,
    );

    expect(client.getCurrentUserId()).toBeNull();
  });

  it("uses HttpOnly cookie credentials instead of localStorage bearer tokens", async () => {
    seedLegacyStoredSession("signed.fixture.token");
    const fetchMock = mockFetchResponse({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    const client = new ApiClient();

    await client.post("/api/tasks/from-email", {
      source_email_id: "<tasks@example.com>",
      items: ["담당자 확인"],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/tasks/from-email",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
    const [, requestInit] = fetchMock.mock.calls[0];
    expect((requestInit as RequestInit).headers).not.toHaveProperty("Authorization");
  });

  it("does not send client-controlled development identity headers", async () => {
    localStorage.setItem("naruon_dev_user", "attacker-selected-user");
    const fetchMock = mockFetchResponse({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    const client = new ApiClient();

    await client.get("/api/emails");

    const [, requestInit] = fetchMock.mock.calls[0];
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-User-Id");
  });

  it("drops caller-supplied public identity headers", async () => {
    const fetchMock = mockFetchResponse({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    const client = new ApiClient();

    await client.get("/api/emails", {
      headers: {
        "X-User-Id": "forged-user",
        "X-Organization-Id": "forged-org",
        "X-Trace-Id": "trace-123",
      },
    });

    const [, requestInit] = fetchMock.mock.calls[0];
    expect((requestInit as RequestInit).headers).toMatchObject({
      "Content-Type": "application/json",
      "X-Trace-Id": "trace-123",
    });
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-User-Id");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-Organization-Id");
  });

  it("strips all public identity headers from browser writes", async () => {
    const fetchMock = mockFetchResponse({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    const client = new ApiClient();

    await client.post(
      "/api/tasks/from-email",
      { messageId: "message-123" },
      {
        headers: {
          "X-User-Id": "forged-user",
          "X-Organization-Id": "forged-org",
          "X-Group-Id": "forged-group",
          "X-Group-Ids": "forged-group-list",
          "X-User-Role": "admin",
          "X-Dev-Auth-Token": "dev-token",
          "X-Trace-Id": "trace-123",
        },
      },
    );

    const [, requestInit] = fetchMock.mock.calls[0];
    expect((requestInit as RequestInit).headers).toMatchObject({
      "Content-Type": "application/json",
      "X-Trace-Id": "trace-123",
    });
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-User-Id");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-Organization-Id");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-Group-Id");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-Group-Ids");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-User-Role");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-Dev-Auth-Token");
  });

  it("drops caller Authorization headers for cookie-authenticated browser writes", async () => {
    seedLegacyStoredSession("signed.fixture.token");
    const fetchMock = mockFetchResponse({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    const client = new ApiClient();

    await client.post(
      "/api/tasks/from-email",
      { messageId: "message-123" },
      {
        headers: {
          Authorization: "Bearer attacker-token",
          authorization: "Bearer lowercase-attacker-token",
        },
      },
    );

    const [, requestInit] = fetchMock.mock.calls[0];
    expect((requestInit as RequestInit).credentials).toBe("include");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("Authorization");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("authorization");
  });
});
