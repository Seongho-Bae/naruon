/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/components/ui/separator", () => ({
  Separator: () => <hr />,
}));

vi.mock("@/components/ui/avatar", () => ({
  Avatar: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AvatarFallback: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/components/ui/checkbox", () => ({
  Checkbox: (props: React.InputHTMLAttributes<HTMLInputElement>) => (
    <input type="checkbox" {...props} />
  ),
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
}));

vi.mock("@/components/ui/textarea", () => ({
  Textarea: (props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) => (
    <textarea {...props} />
  ),
}));

vi.mock("@/components/ui/input", () => ({
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
}));

vi.mock("lucide-react", () => ({
  MessagesSquare: () => <svg aria-hidden="true" />,
}));

import { EmailDetail } from "./EmailDetail";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
};

type TestEmail = {
  id: number;
  message_id: string;
  thread_id: string | null;
  sender: string;
  reply_to?: string | null;
  recipients: string;
  subject: string;
  date: string;
  body: string;
};

function deferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((innerResolve) => {
    resolve = innerResolve;
  });
  return { promise, resolve };
}

function jsonResponse(body: unknown) {
  return {
    ok: true,
    json: async () => body,
  };
}

async function flushAsyncWork() {
  for (let index = 0; index < 5; index += 1) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

async function waitForCondition(condition: () => boolean) {
  for (let index = 0; index < 20; index += 1) {
    if (condition()) return;
    await flushAsyncWork();
  }
}

function backendPathFromInput(input: RequestInfo | URL): string {
  const url = String(input);
  if (!url.startsWith("/api/backend?")) return url;
  return new URL(url, "http://localhost").searchParams.get("path") ?? url;
}

describe("EmailDetail", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    vi.unstubAllGlobals();
  });

  it("keeps the latest conversation when an older thread request resolves late", async () => {
    const emailA: TestEmail = {
      id: 1,
      message_id: "<a@example.com>",
      thread_id: "thread-a",
      sender: "a@example.com",
      recipients: "user@example.com",
      subject: "Thread A",
      date: "2026-04-27T10:00:00Z",
      body: "Selected A body",
    };
    const emailB: TestEmail = {
      id: 2,
      message_id: "<b@example.com>",
      thread_id: "thread-b",
      sender: "b@example.com",
      recipients: "user@example.com",
      subject: "Thread B",
      date: "2026-04-27T11:00:00Z",
      body: "Selected B body",
    };
    const siblingB: TestEmail = {
      ...emailB,
      id: 3,
      message_id: "<b-sibling@example.com>",
      body: "Thread B sibling body",
    };
    const siblingA: TestEmail = {
      ...emailA,
      id: 4,
      message_id: "<a-sibling@example.com>",
      body: "Thread A stale sibling body",
    };

    const emailAResponse = deferred<ReturnType<typeof jsonResponse>>();
    const threadAResponse = deferred<ReturnType<typeof jsonResponse>>();
    const emailBResponse = deferred<ReturnType<typeof jsonResponse>>();
    const threadBResponse = deferred<ReturnType<typeof jsonResponse>>();

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
        const url = backendPathFromInput(input);
        if (url.endsWith("/api/emails/1")) return emailAResponse.promise;
        if (url.endsWith("/api/emails/2")) return emailBResponse.promise;
        if (url.endsWith("/api/emails/thread/thread-a")) return threadAResponse.promise;
        if (url.endsWith("/api/emails/thread/thread-b")) return threadBResponse.promise;
        if (url.endsWith("/api/llm/summarize")) {
          return Promise.resolve(jsonResponse({ summary: "Summary", todos: [] }));
        }
        throw new Error(`Unexpected fetch: ${url}`);
      });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailDetail emailId={1} />);
    });

    await act(async () => {
      emailAResponse.resolve(jsonResponse(emailA));
      await emailAResponse.promise;
    });

    await act(async () => {
      root?.render(<EmailDetail emailId={2} />);
    });

    await act(async () => {
      emailBResponse.resolve(jsonResponse(emailB));
      await emailBResponse.promise;
      await Promise.resolve();
    });

    await waitForCondition(() =>
      fetchMock.mock.calls.some(([input]) =>
        backendPathFromInput(input).endsWith("/api/emails/thread/thread-b"),
      ),
    );

    await act(async () => {
      threadBResponse.resolve(jsonResponse({ thread: [emailB, siblingB] }));
      await threadBResponse.promise;
    });

    await waitForCondition(() =>
      container?.textContent?.includes("Thread B sibling body") ?? false,
    );

    expect(fetchMock.mock.calls.map(([input]) => String(input))).toContain(
      "/api/backend?path=%2Fapi%2Femails%2Fthread%2Fthread-b",
    );
    expect(container.textContent).toContain("Thread B sibling body");
    expect(container.textContent).toContain("2 msgs");

    await act(async () => {
      threadAResponse.resolve(jsonResponse({ thread: [emailA, siblingA] }));
      await threadAResponse.promise;
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("Thread B sibling body");
    expect(container.textContent).toContain("2 msgs");
    expect(container.textContent).not.toContain("Thread A stale sibling body");
  });

  it("clears conversation loading when the latest email has no thread", async () => {
    const threadedEmail: TestEmail = {
      id: 1,
      message_id: "<threaded@example.com>",
      thread_id: "thread-a",
      sender: "threaded@example.com",
      recipients: "user@example.com",
      subject: "Threaded",
      date: "2026-04-27T10:00:00Z",
      body: "Threaded body",
    };
    const standaloneEmail: TestEmail = {
      id: 3,
      message_id: "<standalone@example.com>",
      thread_id: null,
      sender: "standalone@example.com",
      recipients: "user@example.com",
      subject: "Standalone",
      date: "2026-04-27T12:00:00Z",
      body: "Standalone body",
    };

    const threadedEmailResponse = deferred<ReturnType<typeof jsonResponse>>();
    const threadResponse = deferred<ReturnType<typeof jsonResponse>>();
    const standaloneEmailResponse = deferred<ReturnType<typeof jsonResponse>>();

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = backendPathFromInput(input);
      if (url.endsWith("/api/emails/1")) return threadedEmailResponse.promise;
      if (url.endsWith("/api/emails/3")) return standaloneEmailResponse.promise;
      if (url.endsWith("/api/emails/thread/thread-a")) return threadResponse.promise;
      if (url.endsWith("/api/llm/summarize")) {
        return Promise.resolve(jsonResponse({ summary: "Summary", todos: [] }));
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailDetail emailId={1} />);
    });

    await act(async () => {
      threadedEmailResponse.resolve(jsonResponse(threadedEmail));
      await threadedEmailResponse.promise;
      await Promise.resolve();
    });

    await waitForCondition(() =>
      fetchMock.mock.calls.some(([input]) =>
        backendPathFromInput(input).endsWith("/api/emails/thread/thread-a"),
      ),
    );

    await act(async () => {
      root?.render(<EmailDetail emailId={3} />);
    });

    await act(async () => {
      standaloneEmailResponse.resolve(jsonResponse(standaloneEmail));
      await standaloneEmailResponse.promise;
      await Promise.resolve();
    });

    await waitForCondition(() =>
      container?.textContent?.includes("Standalone body") ?? false,
    );

    expect(container.textContent).toContain("Standalone body");
    expect(container.textContent).toContain("1 msgs");
    expect(container.textContent).not.toContain("Loading conversation...");
  });

  it("renders Naruon decision points from thread, reply, and action context", async () => {
    const selectedEmail: TestEmail = {
      id: 4,
      message_id: "<decision@example.com>",
      thread_id: "decision-thread",
      sender: "pm@example.com",
      reply_to: "product-owner@example.com",
      recipients: "user@example.com",
      subject: "Q2 launch decision",
      date: "2026-04-27T12:00:00Z",
      body: "Please confirm the launch plan and risks.",
    };
    const previousMessage: TestEmail = {
      ...selectedEmail,
      id: 5,
      message_id: "<decision-previous@example.com>",
      reply_to: null,
      body: "Earlier context for the launch decision.",
    };

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = backendPathFromInput(input);
      if (url.endsWith("/api/emails/4")) return Promise.resolve(jsonResponse(selectedEmail));
      if (url.endsWith("/api/emails/thread/decision-thread")) {
        return Promise.resolve(jsonResponse({ thread: [previousMessage, selectedEmail] }));
      }
      if (url.endsWith("/api/llm/summarize")) {
        return Promise.resolve(jsonResponse({
          summary: "Launch timing and resource risk need review.",
          todos: ["Confirm resource plan", "Share campaign timing"],
        }));
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailDetail emailId={4} />);
    });

    await waitForCondition(() =>
      container?.textContent?.includes("판단 포인트") ?? false,
    );

    expect(container.textContent).toContain("판단 포인트");
    expect(container.textContent).toContain("4개 점검");
    expect(container.textContent).toContain("대화 흐름 2건");
    expect(container.textContent).toContain("실행 항목 2개");
    expect(container.textContent).toContain("회신 대상 확인");

    const decisionHeading = Array.from(container.querySelectorAll("h3"))
      .find((heading) => heading.textContent === "판단 포인트");

    expect(decisionHeading?.id).toBeTruthy();
    const decisionList = decisionHeading?.id
      ? container.querySelector<HTMLUListElement>(`ul[aria-labelledby="${decisionHeading.id}"]`)
      : null;

    expect(decisionHeading?.className).toContain("text-chart-3");
    expect(decisionList?.getAttribute("aria-labelledby")).toBe(decisionHeading?.id);
    expect(decisionList?.children).toHaveLength(4);
  });

  it("renders untrusted email and LLM content as inert text", async () => {
    const selectedEmail: TestEmail = {
      id: 6,
      message_id: "<xss@example.com>",
      thread_id: "xss-thread",
      sender: "<img src=x onerror=alert('sender')>\u0000@example.com",
      recipients: "user@example.com",
      subject: "<img src=x onerror=alert('subject')>\u0000",
      date: "2026-04-27T12:00:00Z",
      body: "<script>alert('body')</script>\u0000",
    };

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = backendPathFromInput(input);
      if (url.endsWith("/api/emails/6")) return Promise.resolve(jsonResponse(selectedEmail));
      if (url.endsWith("/api/emails/thread/xss-thread")) {
        return Promise.resolve(jsonResponse({ thread: [selectedEmail] }));
      }
      if (url.endsWith("/api/llm/summarize")) {
        return Promise.resolve(jsonResponse({
          summary: "<svg onload=alert('summary')>\u0000",
          todos: ["<img src=x onerror=alert('todo')>\u0000"],
        }));
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailDetail emailId={6} />);
    });

    await waitForCondition(() =>
      container?.textContent?.includes("<img src=x onerror=alert('subject')>") ?? false,
    );

    expect(container.querySelector("img, script")).toBeNull();
    expect(container.textContent).toContain("<script>alert('body')</script>");
    expect(container.textContent).not.toContain("\u0000");
  });
});
