import { describe, expect, it } from "vitest";

import { safeReturnTo } from "./shared";

describe("safeReturnTo", () => {
  it("allows local paths with query strings and fragments", () => {
    expect(safeReturnTo("/settings?tab=security#oidc")).toBe(
      "/settings?tab=security#oidc",
    );
  });

  it.each([
    "https://evil.example/phish",
    "//evil.example/phish",
    "/%2f%2fevil.example/phish",
    "/%5c%5cevil.example/phish",
    "/%09/evil.example/phish",
    "/\\evil.example/phish",
    "settings",
  ])("rejects unsafe return target %s", (target) => {
    expect(safeReturnTo(target)).toBe("/");
  });
});
