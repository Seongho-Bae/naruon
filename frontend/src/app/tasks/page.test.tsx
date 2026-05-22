/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("lucide-react", () => ({
  CheckCircle2: () => <svg aria-hidden="true" />,
  Inbox: () => <svg aria-hidden="true" />,
  ListChecks: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  UserRoundCheck: () => <svg aria-hidden="true" />,
}));

import TasksPage from "./page";

function jsonResponse(body: unknown, ok = true) {
  return {
    ok,
    status: ok ? 200 : 500,
    statusText: ok ? "OK" : "Server Error",
    json: async () => body,
  } as Response;
}

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

describe("TasksPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("renders ticket tracking screens with source-linked task details", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse([])));
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<TasksPage />);
    });
    await flushAsyncWork();

    expect(container.querySelector("h1")?.textContent).toContain("할 일 추적");
    expect(container.textContent).toContain("내 작업");
    expect(container.textContent).toContain("위임한 작업");
    expect(container.textContent).toContain("칸반");
    expect(container.textContent).toContain("작업 상세");
    expect(container.textContent).toContain("접수");
    expect(container.textContent).toContain("진행");
    expect(container.textContent).toContain("차단");
    expect(container.textContent).toContain("완료");
    expect(container.textContent).toContain("원본 메일");
    expect(container.textContent).toContain("답변 추적");
    expect(container.textContent).not.toContain("Ticket tasks");
    expect(container.textContent).not.toContain("다음 구현 단계");
  });

  it("loads source-linked tickets from the signed session tasks API without public identity headers", async () => {
    const fetchMock = vi.fn(async (...args: [RequestInfo | URL, RequestInit?]) => {
      void args;
      return jsonResponse([
        {
          id: "task_01HZXOPAQUE001",
          title: "파트너 일정 후보 확인",
          status: "blocked",
          priority: "urgent",
          source_type: "email",
          source_email_id: "<partner-thread@example.com>",
          related_thread_id: "thread-partner-q3",
          created_at: "2026-05-19T00:00:00Z",
          updated_at: "2026-05-21T00:00:00Z",
        },
      ]);
    });
    vi.stubGlobal("fetch", fetchMock);
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<TasksPage />);
    });
    await flushAsyncWork();

    expect(fetchMock).toHaveBeenCalledWith("/api/tasks", expect.objectContaining({
      credentials: "include",
    }));
    const firstCall = fetchMock.mock.calls[0];
    expect(firstCall).toBeDefined();
    const [, init] = firstCall as [RequestInfo | URL, RequestInit?];
    const headers = init?.headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
    expect(headers["X-User-Id"]).toBeUndefined();
    expect(headers["X-Organization-Id"]).toBeUndefined();
    expect(headers["X-Group-Id"]).toBeUndefined();
    expect(headers["X-Group-Ids"]).toBeUndefined();
    expect(headers["X-User-Role"]).toBeUndefined();
    expect(headers["X-Dev-Auth-Token"]).toBeUndefined();
    expect(container.textContent).toContain("파트너 일정 후보 확인");
    expect(container.textContent).toContain("긴급");
    expect(container.textContent).toContain("차단");
    expect(container.textContent).toContain("<partner-thread@example.com>");
    expect(container.textContent).toContain("thread-partner-q3");
  });
});
