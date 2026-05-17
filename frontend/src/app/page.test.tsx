/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

const mockEmailSelection = vi.hoisted(() => ({ emailId: 42 }));
const mockDetailCommands = vi.hoisted(() => ({ executions: [] as string[] }));

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
  }) => {
    React.useEffect(() => {
      if (emailId !== null && actionCommand) {
        mockDetailCommands.executions.push(`${emailId}:${actionCommand.action}:${actionCommand.id}`);
      }
    }, [actionCommand, emailId]);

    return (
      <section aria-label="mock email detail">
        <span>email:{emailId ?? "none"}</span>
        <span>action:{actionCommand?.action ?? "none"}</span>
      </section>
    );
  },
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
    mockDetailCommands.executions = [];
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
    expect(mockDetailCommands.executions).toEqual(["42:calendar-sync:1"]);
    expect(container.textContent).not.toContain("먼저 메일을 선택하세요.");
  });

  it("does not replay a desktop shell action after a desktop-tablet-desktop resize", async () => {
    const mobileListeners = new Set<(event: MediaQueryListEvent) => void>();
    const tabletListeners = new Set<(event: MediaQueryListEvent) => void>();
    let mobileMatches = false;
    let tabletMatches = false;
    vi.stubGlobal("matchMedia", vi.fn((query: string) => ({
      get matches() {
        if (query.includes("max-width: 1023px")) return mobileMatches;
        return query.includes("min-width: 1024px") ? tabletMatches : false;
      },
      media: query,
      addEventListener: (_event: "change", listener: (event: MediaQueryListEvent) => void) => {
        if (query.includes("max-width: 1023px")) mobileListeners.add(listener);
        if (query.includes("min-width: 1024px")) tabletListeners.add(listener);
      },
      removeEventListener: (_event: "change", listener: (event: MediaQueryListEvent) => void) => {
        mobileListeners.delete(listener);
        tabletListeners.delete(listener);
      },
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

    expect(mockDetailCommands.executions).toEqual(["42:reply-draft:1"]);

    await act(async () => {
      mobileMatches = true;
      mobileListeners.forEach((listener) => listener({ matches: true } as MediaQueryListEvent));
    });
    await flushAsyncWork();

    expect(mockDetailCommands.executions).toEqual(["42:reply-draft:1"]);

    await act(async () => {
      mobileMatches = false;
      mobileListeners.forEach((listener) => listener({ matches: false } as MediaQueryListEvent));
    });
    await flushAsyncWork();

    expect(mockDetailCommands.executions).toEqual(["42:reply-draft:1"]);
    expect(countText(container.textContent ?? "", "email:42")).toBe(1);

    await act(async () => {
      tabletMatches = true;
      tabletListeners.forEach((listener) => listener({ matches: true } as MediaQueryListEvent));
    });
    await flushAsyncWork();

    expect(mockDetailCommands.executions).toEqual(["42:reply-draft:1"]);

    await act(async () => {
      tabletMatches = false;
      tabletListeners.forEach((listener) => listener({ matches: false } as MediaQueryListEvent));
    });
    await flushAsyncWork();

    expect(mockDetailCommands.executions).toEqual(["42:reply-draft:1"]);
  });

  it("unmounts the mobile detail pane after returning from mobile to desktop", async () => {
    const mobileListeners = new Set<(event: MediaQueryListEvent) => void>();
    let mobileMatches = true;
    vi.stubGlobal("matchMedia", vi.fn((query: string) => ({
      get matches() {
        return query.includes("max-width: 1023px") ? mobileMatches : false;
      },
      media: query,
      addEventListener: (_event: "change", listener: (event: MediaQueryListEvent) => void) => {
        if (query.includes("max-width: 1023px")) mobileListeners.add(listener);
      },
      removeEventListener: (_event: "change", listener: (event: MediaQueryListEvent) => void) => {
        mobileListeners.delete(listener);
      },
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

    expect(countText(container.textContent ?? "", "email:42")).toBe(1);
    expect(mockDetailCommands.executions).toEqual(["42:reply-draft:1"]);

    await act(async () => {
      mobileMatches = false;
      mobileListeners.forEach((listener) => listener({ matches: false } as MediaQueryListEvent));
    });
    await flushAsyncWork();

    expect(countText(container.textContent ?? "", "email:42")).toBe(1);
    expect(mockDetailCommands.executions).toEqual(["42:reply-draft:1"]);

    await act(async () => {
      mobileMatches = true;
      mobileListeners.forEach((listener) => listener({ matches: true } as MediaQueryListEvent));
    });
    await flushAsyncWork();

    expect(mockDetailCommands.executions).toEqual(["42:reply-draft:1"]);
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
    expect(window.location.hash).toBe("");
  });

  it("includes a tablet workspace with a collapsed context panel", async () => {
    vi.stubGlobal("matchMedia", vi.fn((query: string) => ({
      matches: query.includes("min-width: 1024px"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })));
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });
    await flushAsyncWork();

    expect(container.querySelector('[aria-label="태블릿 메일 작업공간"]')).not.toBeNull();
    expect(container.querySelector('details[aria-label="태블릿 맥락 그래프"]')?.textContent).toContain("태블릿 맥락 패널");
    expect(container.textContent).toContain("맥락 그래프는 필요할 때 펼쳐서 확인합니다.");
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
    expect(window.location.hash).toBe("");
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

  it("renders an API-backed loading state for the mobile search panel instead of placeholders", async () => {
    vi.stubGlobal("matchMedia", vi.fn(() => ({
      matches: true,
      media: "(max-width: 1023px)",
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })));
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));
    window.history.replaceState(null, "", "/#mobile-search");
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });
    await flushAsyncWork();

    expect(container.querySelector('#mobile-search')?.className).toContain("flex");
    expect(container.textContent).toContain("검색 결과를 불러오는 중입니다.");
    expect(container.textContent).not.toContain("메일 결과 준비 중");
    expect(fetch).toHaveBeenCalledWith("/api/search", expect.objectContaining({ method: "POST" }));
  });

  it("renders an API-backed loading state for the mobile calendar panel instead of static candidates", async () => {
    vi.stubGlobal("matchMedia", vi.fn(() => ({
      matches: true,
      media: "(max-width: 1023px)",
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })));
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));
    window.history.replaceState(null, "", "/#mobile-calendar");
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<Home />);
    });
    await flushAsyncWork();

    expect(container.querySelector('#mobile-calendar')?.className).toContain("flex");
    expect(container.textContent).toContain("일정 후보를 불러오는 중입니다.");
    expect(container.textContent).not.toContain("디자인 리뷰 후속 조치");
    expect(fetch).toHaveBeenCalledWith("/api/search", expect.objectContaining({ method: "POST" }));
  });
});
