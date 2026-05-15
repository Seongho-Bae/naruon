/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

const apiClientMock = vi.hoisted(() => ({
  getBearerToken: vi.fn(() => null),
}));

const runtimeConfigMock = vi.hoisted(() => vi.fn(async () => ({
  features: {
    dev_header_auth_enabled: true,
  },
})));

vi.mock("@/lib/api-client", () => ({
  apiClient: apiClientMock,
}));

vi.mock("@/lib/runtime-config", () => ({
  getRuntimeConfig: runtimeConfigMock,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
}));

vi.mock("lucide-react", () => ({
  UserCircle: () => <svg aria-hidden="true" />,
}));

import { DevAuthSwitcher } from "./DevAuthSwitcher";

async function flushAsyncWork() {
  for (let index = 0; index < 3; index += 1) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

describe("DevAuthSwitcher", () => {
  const originalLocation = window.location;
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    window.localStorage.clear();
    Object.defineProperty(window, "location", {
      configurable: true,
      value: originalLocation,
    });
    vi.clearAllMocks();
    apiClientMock.getBearerToken.mockReturnValue(null);
    runtimeConfigMock.mockResolvedValue({
      features: {
        dev_header_auth_enabled: true,
      },
    });
  });

  it("hides the dev switcher on private LAN hosts even when runtime dev headers are enabled", async () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: new URL("http://192.168.0.12:3000/settings"),
    });

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<DevAuthSwitcher />);
    });
    await flushAsyncWork();

    expect(container.textContent).not.toContain("관리자 (Admin)");
    expect(container.textContent).not.toContain("일반 (Member)");
  });

  it("keeps the legacy dev switcher hidden on localhost", async () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: new URL("http://localhost:3000/settings"),
    });

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<DevAuthSwitcher />);
    });
    await flushAsyncWork();

    expect(container.textContent).not.toContain("관리자 (Admin)");
    expect(container.textContent).not.toContain("일반 (Member)");
  });
});
