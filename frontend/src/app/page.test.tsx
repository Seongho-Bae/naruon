/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

const mockEmailSelection = vi.hoisted(() => ({ emailId: 42 }));

vi.mock("@/components/EmailList", () => ({
  EmailList: ({ onSelectEmail }: { onSelectEmail: (emailId: number) => void }) => (
    <button type="button" onClick={() => onSelectEmail(mockEmailSelection.emailId)}>메일 선택</button>
  ),
}));

vi.mock("@/components/EmailDetail", () => ({
  EmailDetail: ({
    emailId,
    actionCommand,
  }: {
    emailId: number | null;
    actionCommand?: { action: string; id: number } | null;
  }) => (
    <section aria-label="mock email detail">
      <span>email:{emailId ?? "none"}</span>
      <span>action:{actionCommand?.action ?? "none"}</span>
    </section>
  ),
}));

vi.mock("@/components/ui/resizable", () => ({
  ResizablePanelGroup: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ResizablePanel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ResizableHandle: () => <div />,
}));

vi.mock("next/dynamic", () => ({
  default: () => function MockDynamic() {
    return <div>mock graph</div>;
  },
}));

vi.mock("lucide-react", () => ({
  Network: () => <svg aria-hidden="true" />,
}));

import Home from "./page";

function countText(haystack: string, needle: string) {
  return haystack.split(needle).length - 1;
}

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

describe("Home workspace action bridge", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    mockEmailSelection.emailId = 42;
    vi.unstubAllGlobals();
  });

  it("asks users to choose an email before running a shell action", async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });

    await act(async () => {
      window.dispatchEvent(new CustomEvent("naruon:header-action", { detail: { action: "reply-draft" } }));
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("먼저 메일을 선택하세요.");
    expect(container.textContent).toContain("action:none");
  });

  it("forwards shell actions to the selected email detail", async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });

    await act(async () => {
      container?.querySelector<HTMLButtonElement>("button")?.click();
    });
    await act(async () => {
      window.dispatchEvent(new CustomEvent("naruon:header-action", { detail: { action: "calendar-sync" } }));
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("email:42");
    expect(container.textContent).toContain("action:calendar-sync");
    expect(countText(container.textContent ?? "", "action:calendar-sync")).toBe(1);
    expect(container.textContent).not.toContain("먼저 메일을 선택하세요.");
  });

  it("does not replay a stale mobile shell action after returning to the inbox", async () => {
    const listeners = new Set<(event: MediaQueryListEvent) => void>();
    vi.stubGlobal("matchMedia", vi.fn(() => ({
      matches: true,
      media: "(max-width: 1023px)",
      addEventListener: (_event: "change", listener: (event: MediaQueryListEvent) => void) => listeners.add(listener),
      removeEventListener: (_event: "change", listener: (event: MediaQueryListEvent) => void) => listeners.delete(listener),
    })));

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });

    await act(async () => {
      container?.querySelector<HTMLButtonElement>("button")?.click();
    });
    await act(async () => {
      window.dispatchEvent(new CustomEvent("naruon:header-action", { detail: { action: "reply-draft" } }));
    });
    await flushAsyncWork();

    expect(countText(container.textContent ?? "", "action:reply-draft")).toBe(1);

    await act(async () => {
      Array.from(container?.querySelectorAll<HTMLButtonElement>("button") ?? [])
        .find((button) => button.textContent?.includes("목록으로"))
        ?.click();
    });
    mockEmailSelection.emailId = 43;
    await act(async () => {
      container?.querySelector<HTMLButtonElement>("button")?.click();
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("email:43");
    expect(container.textContent).toContain("action:none");
    expect(container.textContent).not.toContain("action:reply-draft");
  });
});
