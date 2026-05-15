import { describe, expect, it } from "vitest";

import { metadata } from "./layout";

describe("root layout metadata", () => {
  it("describes the Korean-first Naruon workspace and local icons", () => {
    expect(metadata.title).toBe("Naruon | 메일 워크스페이스");
    expect(metadata.description).toContain("이메일");
    expect(metadata.description).toContain("일정");
    expect(metadata.description).toContain("관계");
    expect(metadata.description).toContain("판단 포인트");
    expect(metadata.description).not.toContain("AI 이메일");
    expect(metadata.icons).toMatchObject({
      icon: "/brand/naruon-app-icon.svg",
    });
  });
});
