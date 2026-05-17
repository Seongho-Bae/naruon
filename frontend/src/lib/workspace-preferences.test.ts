/* @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from "vitest";

import { getWorkspaceStartupView, setWorkspaceStartupView } from "./workspace-preferences";

describe("workspace startup preferences", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("falls back to email when localStorage reads throw", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("blocked", "SecurityError");
    });

    expect(getWorkspaceStartupView()).toBe("email");
  });

  it("does not throw or skip notification when localStorage writes throw", () => {
    const listener = vi.fn();
    window.addEventListener("naruon:startup-view-change", listener);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("blocked", "SecurityError");
    });

    expect(() => setWorkspaceStartupView("calendar")).not.toThrow();
    expect(listener).toHaveBeenCalledTimes(1);

    window.removeEventListener("naruon:startup-view-change", listener);
  });
});
