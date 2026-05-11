import { describe, expect, it } from "vitest";

describe("Vitest React setup", () => {
  it("enables the React act environment globally", () => {
    expect(globalThis.IS_REACT_ACT_ENVIRONMENT).toBe(true);
  });
});
