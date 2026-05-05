import { afterEach, describe, expect, it } from "vitest";

import { buildApiHeaders } from "./api-client";

describe("buildApiHeaders", () => {
  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_AUTH_TOKEN;
  });

  it("preserves existing headers when no local API token is configured", () => {
    delete process.env.NEXT_PUBLIC_API_AUTH_TOKEN;

    const headers = buildApiHeaders({ "Content-Type": "application/json" });

    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.has("Authorization")).toBe(false);
  });

  it("adds the configured local bearer token without dropping existing headers", () => {
    process.env.NEXT_PUBLIC_API_AUTH_TOKEN = "  local-token  ";

    const headers = buildApiHeaders({ "Content-Type": "application/json" });

    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("Authorization")).toBe("Bearer local-token");
  });
});
