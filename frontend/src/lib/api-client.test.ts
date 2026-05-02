import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch, backendApiUrl } from "./api-client";


describe("apiFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("routes backend API paths through the same-origin proxy", () => {
    expect(backendApiUrl("/api/emails")).toBe("/api/backend/api/emails");
    expect(backendApiUrl("api/network/graph")).toBe(
      "/api/backend/api/network/graph",
    );
  });

  it("does not add browser-side authentication to fetch calls", async () => {
    const fetchMock = vi.fn(() => Promise.resolve({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/api/backend/api/emails");

    expect(fetchMock).toHaveBeenCalledWith("/api/backend/api/emails");
  });

  it("preserves caller headers without adding browser-side authentication", async () => {
    const fetchMock = vi.fn(() => Promise.resolve({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/api/backend/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "demo" }),
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/backend/api/search",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: "demo" }),
      },
    );
  });
});
