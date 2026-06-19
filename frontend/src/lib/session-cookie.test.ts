import { describe, expect, it } from "vitest";

import { normalizeSessionToken } from "./session-cookie";

describe("normalizeSessionToken", () => {
  it("accepts compact JWT-shaped bearer session tokens", () => {
    expect(normalizeSessionToken(" header.payload.signature ")).toBe(
      "header.payload.signature",
    );
    expect(normalizeSessionToken("hdr_segment.payload_segment.sig_segment")).toBe(
      "hdr_segment.payload_segment.sig_segment",
    );
  });

  it("rejects empty, control-character, oversized, and non-JWT token values", () => {
    expect(normalizeSessionToken("")).toBeNull();
    expect(normalizeSessionToken("signed-session-token")).toBeNull();
    expect(normalizeSessionToken("header.payload")).toBeNull();
    expect(normalizeSessionToken("header.payload.signature.extra")).toBeNull();
    expect(normalizeSessionToken("<script>alert(1)</script>")).toBeNull();
    expect(normalizeSessionToken("header.pay\nload.signature")).toBeNull();
    expect(normalizeSessionToken("a".repeat(4097))).toBeNull();
    expect(normalizeSessionToken(null)).toBeNull();
  });
});
