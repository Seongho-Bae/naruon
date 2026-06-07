import { describe, expect, it } from "vitest";

import { metadata } from "./layout";

describe("root layout metadata", () => {
  it("describes the Korean-first Naruon workspace and local icons", () => {
    expect(metadata.title).toBe("Naruon | AI Email Workspace");
    expect(metadata.description).toContain("이메일");
    expect(metadata.icons).toMatchObject({
      icon: "/brand/naruon-app-icon.svg",
    });
  });
});
