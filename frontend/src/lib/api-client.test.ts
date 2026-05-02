import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch, backendApiUrl } from "./api-client";


describe("apiFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("routes backend API paths through the same-origin proxy", () => {
    expect(backendApiUrl("/api/emails")).toBe("/api/backend?path=%2Fapi%2Femails");
    expect(backendApiUrl("api/network/graph")).toBe(
      "/api/backend?path=%2Fapi%2Fnetwork%2Fgraph",
    );
  });

  it("does not add browser-side authentication to fetch calls", async () => {
    const fetchMock = vi.fn(() => Promise.resolve({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch(backendApiUrl("/api/emails"));

    expect(fetchMock).toHaveBeenCalledWith("/api/backend?path=%2Fapi%2Femails");
  });

  it("preserves caller headers without adding browser-side authentication", async () => {
    const fetchMock = vi.fn(() => Promise.resolve({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch(backendApiUrl("/api/search"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "demo" }),
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/backend?path=%2Fapi%2Fsearch",
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
