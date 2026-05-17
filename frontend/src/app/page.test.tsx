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
  CalendarDays: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  Inbox: () => <svg aria-hidden="true" />,
  Network: () => <svg aria-hidden="true" />,
  Sparkles: () => <svg aria-hidden="true" />,
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
    localStorage.clear();
    window.history.replaceState(null, "", "/");
    Reflect.deleteProperty(window, "__naruonMobileWorkspace");
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

  it("defaults to the email workspace when no startup preference is saved", async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("메일 선택");
    expect(container.textContent).toContain("email:none");
    expect(container.textContent).not.toContain("오늘의 실행 대시보드");
  });

  it("opens the saved calendar startup view on mobile without needing a hash", async () => {
    vi.stubGlobal("matchMedia", vi.fn(() => ({
      matches: true,
      media: "(max-width: 1023px)",
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })));
    localStorage.setItem("naruon_startup_view", "calendar");
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });
    await flushAsyncWork();

    expect(container.querySelector('#mobile-calendar')?.className).toContain("flex");
    expect(container.textContent).toContain("캘린더 반영 대기");
  });

  it("shows the saved dashboard startup view until users switch back to email", async () => {
    localStorage.setItem("naruon_startup_view", "dashboard");
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("오늘의 실행 대시보드");
    expect(container.textContent).toContain("이메일 작업공간 열기");

    await act(async () => {
      Array.from(container?.querySelectorAll<HTMLButtonElement>("button") ?? [])
        .find((button) => button.textContent?.includes("이메일 작업공간 열기"))
        ?.click();
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("메일 선택");
    expect(container.textContent).toContain("email:none");
  });

  it("lets a mobile hash deep link override a saved dashboard startup view", async () => {
    vi.stubGlobal("matchMedia", vi.fn(() => ({
      matches: true,
      media: "(max-width: 1023px)",
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })));
    localStorage.setItem("naruon_startup_view", "dashboard");
    window.history.replaceState(null, "", "/#mobile-calendar");
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });
    await flushAsyncWork();

    expect(container.querySelector('#mobile-calendar')?.className).toContain("flex");
    expect(container.textContent).toContain("캘린더 반영 대기");
    expect(container.textContent).not.toContain("오늘의 실행 대시보드");
  });
});
