import { describe, expect, it } from "vitest";

import {
  normalizeSessionToken,
  buildSessionCookieOptions,
  buildExpiredSessionCookieOptions,
  SESSION_COOKIE_NAME,
  SESSION_COOKIE_MAX_AGE_SECONDS,
} from "./session-cookie";

describe("normalizeSessionToken", () => {
  it("accepts compact JWT-shaped bearer session tokens", () => {
    expect(normalizeSessionToken(" header.payload.signature ")).toBe(
      "header.payload.signature",
    );
    expect(normalizeSessionToken("hdr_segment.payload_segment.sig_segment")).toBe(
      "hdr_segment.payload_segment.sig_segment",
    );
  });

  describe("rejects invalid types", () => {
    it("rejects non-string values", () => {
      expect(normalizeSessionToken(null)).toBeNull();
      expect(normalizeSessionToken(undefined)).toBeNull();
      expect(normalizeSessionToken(123)).toBeNull();
      expect(normalizeSessionToken({})).toBeNull();
      expect(normalizeSessionToken([])).toBeNull();
      expect(normalizeSessionToken(true)).toBeNull();
    });
  });

  describe("rejects empty or whitespace tokens", () => {
    it("rejects empty strings", () => {
      expect(normalizeSessionToken("")).toBeNull();
    });

    it("rejects whitespace-only strings", () => {
      expect(normalizeSessionToken("   ")).toBeNull();
      expect(normalizeSessionToken("\t\n")).toBeNull();
    });
  });

  describe("enforces maximum length", () => {
    it("accepts valid token exactly 4096 characters long", () => {
      const token4096 = "a".repeat(1000) + "." + "b".repeat(1000) + "." + "c".repeat(2094);
      expect(normalizeSessionToken(token4096)).toBe(token4096);
    });

    it("rejects token exceeding 4096 characters", () => {
      const token4097 = "a".repeat(1000) + "." + "b".repeat(1000) + "." + "c".repeat(2095);
      expect(normalizeSessionToken(token4097)).toBeNull();
    });
  });

  describe("rejects control characters", () => {
    it("rejects tokens with null bytes", () => {
      expect(normalizeSessionToken("head\u0000er.payload.signature")).toBeNull();
    });

    it("rejects tokens with newlines", () => {
      expect(normalizeSessionToken("header.pay\nload.signature")).toBeNull();
    });

    it("rejects tokens with other control characters", () => {
      expect(normalizeSessionToken("header.payload.signature\u001f")).toBeNull();
      expect(normalizeSessionToken("header.payload.signature\u007f")).toBeNull();
    });
  });

  describe("enforces JWT pattern", () => {
    it("rejects tokens with missing segments", () => {
      expect(normalizeSessionToken("header.payload")).toBeNull();
      expect(normalizeSessionToken("header")).toBeNull();
    });

    it("rejects tokens with too many segments", () => {
      expect(normalizeSessionToken("header.payload.signature.extra")).toBeNull();
    });

    it("rejects tokens with invalid characters in segments", () => {
      expect(normalizeSessionToken("header.payload!.signature")).toBeNull();
      expect(normalizeSessionToken("<script>alert(1)</script>")).toBeNull();
      expect(normalizeSessionToken("header.payload.sig@nature")).toBeNull();
    });
  });
});

describe("buildSessionCookieOptions", () => {
  it("returns correct cookie options for a valid token", () => {
    const token = "header.payload.signature";
    const options = buildSessionCookieOptions(token);

    expect(options).toEqual({
      name: SESSION_COOKIE_NAME,
      value: token,
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      path: "/",
      maxAge: SESSION_COOKIE_MAX_AGE_SECONDS,
    });
  });
});

describe("buildExpiredSessionCookieOptions", () => {
  it("returns correct cookie options to expire the cookie", () => {
    const options = buildExpiredSessionCookieOptions();

    expect(options).toEqual({
      name: SESSION_COOKIE_NAME,
      value: "",
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      path: "/",
      maxAge: 0,
    });
  });
});
