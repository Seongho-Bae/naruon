/* @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClient } from "./api-client";

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

describe("ApiClient", () => {
  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("does not derive display user context from browser-readable storage", () => {
    localStorage.setItem("naruon_dev_user", "legacy-dev-user");
    const client = new ApiClient();

    expect(client.getCurrentUserId()).toBeNull();

    localStorage.setItem("legacy_browser_context", "legacy.browser.value");

    expect(client.getCurrentUserId()).toBeNull();
  });

  it("does not send browser-readable session tokens", async () => {
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
        headers: expect.not.objectContaining({ Authorization: expect.any(String) }),
      }),
    );
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

  it("drops caller-supplied Authorization headers", async () => {
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
    expect((requestInit as RequestInit).headers).not.toHaveProperty("Authorization");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("authorization");
  });

  it("sends multipart form data without browser auth or caller identity headers", async () => {
    const fetchMock = mockFetchResponse({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    const client = new ApiClient();
    const formData = new FormData();
    formData.append("files", new File(["raw email"], "source.eml", { type: "message/rfc822" }));

    await client.postForm("/api/emails/import-files", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
        "X-User-Id": "forged-user",
        "X-Trace-Id": "trace-456",
      },
    });

    const [, requestInit] = fetchMock.mock.calls[0];
    expect(requestInit?.method).toBe("POST");
    expect(requestInit?.body).toBe(formData);
    expect((requestInit as RequestInit).headers).toMatchObject({
      "X-Trace-Id": "trace-456",
    });
    expect((requestInit as RequestInit).headers).not.toHaveProperty("Authorization");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("Content-Type");
    expect((requestInit as RequestInit).headers).not.toHaveProperty("X-User-Id");
  });

  it("reads non-sensitive session claims from the server session route", async () => {
    const fetchMock = mockFetchResponse({
      authenticated: true,
      claims: {
        userId: "signed-user",
        organizationId: "org-acme",
        workspaceId: "workspace-acme",
      },
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new ApiClient();

    await expect(client.getServerSessionClaims()).resolves.toEqual({
      userId: "signed-user",
      organizationId: "org-acme",
      workspaceId: "workspace-acme",
    });
    expect(fetchMock).toHaveBeenCalledWith("/auth/session", {
      method: "GET",
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    });
  });

  it("fails closed to anonymous claims when the server session route is unavailable", async () => {
    const fetchMock = vi.fn(async () => {
      throw new Error("network unavailable");
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new ApiClient();

    await expect(client.getServerSessionClaims()).resolves.toEqual({
      userId: null,
      organizationId: null,
      workspaceId: null,
    });
  });
});
