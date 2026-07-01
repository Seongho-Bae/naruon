/* @vitest-environment jsdom */
import { describe, expect, it } from "vitest";

describe("Vitest React setup", () => {
  it("enables the React act environment globally", () => {
    expect(globalThis.IS_REACT_ACT_ENVIRONMENT).toBe(true);
  });

  it("provides browser storage in jsdom tests", () => {
    expect(window.localStorage).toBeDefined();
    window.localStorage.setItem("naruon_test_storage", "ready");
    expect(window.localStorage.getItem("naruon_test_storage")).toBe("ready");
  });
});
