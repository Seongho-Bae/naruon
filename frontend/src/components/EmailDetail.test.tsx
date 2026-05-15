/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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
import { apiClient } from "@/lib/api-client";

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
};

type TestEmail = {
  id: number;
  mailbox_account_id?: number | null;
  message_id: string;
  thread_id: string | null;
  sender: string;
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

describe("EmailDetail", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  beforeEach(() => {
    apiClient.setBaseUrl('');
    apiClient.setDevHeaderAuthEnabled(true);
  });

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
      mailbox_account_id: 1,
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
      mailbox_account_id: 2,
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
        const url = String(input);
        if (url.endsWith("/api/emails/1")) return emailAResponse.promise;
        if (url.endsWith("/api/emails/2")) return emailBResponse.promise;
        if (url.endsWith("/api/emails/thread/thread-a?mailbox_account_id=1")) return threadAResponse.promise;
        if (url.endsWith("/api/emails/thread/thread-b?mailbox_account_id=2")) return threadBResponse.promise;
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
        String(input).endsWith("/api/emails/thread/thread-b?mailbox_account_id=2"),
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
      "/api/emails/thread/thread-b?mailbox_account_id=2",
    );
    expect(container.textContent).toContain("Thread B sibling body");
    expect(container.textContent).toContain("2개 메시지");

    await act(async () => {
      threadAResponse.resolve(jsonResponse({ thread: [emailA, siblingA] }));
      await threadAResponse.promise;
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("Thread B sibling body");
    expect(container.textContent).toContain("2개 메시지");
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
      const url = String(input);
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
        String(input).endsWith("/api/emails/thread/thread-a"),
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
    expect(container.textContent).toContain("1개 메시지");
    expect(container.textContent).not.toContain("대화 흐름을 불러오는 중입니다...");
  });

  it("uses the selected mailbox scope for legacy emails without mailbox ids", async () => {
    const legacyEmail: TestEmail = {
      id: 9,
      mailbox_account_id: null,
      message_id: "<legacy@example.com>",
      thread_id: "legacy-thread",
      sender: "legacy@example.com",
      recipients: "user@example.com",
      subject: "Legacy",
      date: "2026-04-27T10:00:00Z",
      body: "Legacy body",
    };

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/emails/9")) return Promise.resolve(jsonResponse(legacyEmail));
      if (url.endsWith("/api/emails/thread/legacy-thread?mailbox_account_id=2")) {
        return Promise.resolve(jsonResponse({ thread: [legacyEmail] }));
      }
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
      root?.render(<EmailDetail emailId={9} mailboxAccountId={2} />);
    });
    await flushAsyncWork();

    expect(fetchMock.mock.calls.map(([input]) => String(input))).toContain(
      "/api/emails/thread/legacy-thread?mailbox_account_id=2",
    );
  });

  it("uses Korean-first labels for AI summary and execution actions", async () => {
    const email: TestEmail = {
      id: 5,
      message_id: "<label@example.com>",
      thread_id: null,
      sender: "label@example.com",
      recipients: "user@example.com",
      subject: "Label check",
      date: "2026-05-11T09:00:00Z",
      body: "Please review the launch plan.",
    };

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/emails/5")) return Promise.resolve(jsonResponse(email));
      if (url.endsWith("/api/llm/summarize")) {
        return Promise.resolve(jsonResponse({ summary: "출시 계획 검토", todos: ["일정 확인"] }));
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailDetail emailId={5} />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("맥락 종합");
    expect(container.textContent).toContain("AI 생성");
    expect(container.textContent).toContain("실행 항목");
    expect(container.textContent).toContain("1개 실행 항목");
    expect(container.textContent).not.toContain("AI Generated");
    expect(container.textContent).not.toContain("Tasks");
  });
});
