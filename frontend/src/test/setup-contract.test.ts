/* @vitest-environment jsdom */
import { describe, expect, it } from "vitest";

describe("Vitest React setup", () => {
  it("enables the React act environment globally", () => {
    expect(globalThis.IS_REACT_ACT_ENVIRONMENT).toBe(true);
  });

  it("provides browser storage in jsdom tests", () => {
    const key = "naruon_test_storage";
    expect(window.localStorage).toBeDefined();
    try {
      window.localStorage.setItem(key, "ready");
      expect(window.localStorage.getItem(key)).toBe("ready");
    } finally {
      window.localStorage.removeItem(key);
    }
  });
});
