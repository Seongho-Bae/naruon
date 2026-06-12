import { describe, expect, it } from "vitest";
import type { SettingsTab } from "../src/components/SettingsLayout";

describe("SettingsTab", () => {
  it("uses the Korean-first settings destinations", () => {
    const tabs: SettingsTab[] = [
      "워크스페이스",
      "멤버",
      "AI 모델",
      "연결 계정",
      "알림",
      "자동화",
      "결제",
      "개발자",
    ];

    expect(tabs).toContain("AI 모델");
    expect(tabs).toContain("연결 계정");
  });
});
