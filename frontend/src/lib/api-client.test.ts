/* @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClient } from "./api-client";

function jsonResponse(body: unknown) {
  return {
    ok: true,
    json: async () => body,
  };
}

describe("ApiClient", () => {
  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("sends the signed bearer session token when one is stored", async () => {
    localStorage.setItem("naruon_session_token", "signed.fixture.token");
    const fetchMock = vi.fn(() => Promise.resolve(jsonResponse({ ok: true })));
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
        headers: expect.objectContaining({
          Authorization: "Bearer signed.fixture.token",
        }),
      }),
    );
  });
});
