/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("lucide-react", () => ({
  AlertCircle: () => <svg aria-hidden="true" />,
  CalendarDays: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  Filter: () => <svg aria-hidden="true" />,
  Inbox: () => <svg aria-hidden="true" />,
  ListChecks: () => <svg aria-hidden="true" />,
  MoreHorizontal: () => <svg aria-hidden="true" />,
  Search: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  User: () => <svg aria-hidden="true" />,
  UserRoundCheck: () => <svg aria-hidden="true" />,
  Plus: () => <svg aria-hidden="true" />,
}));

import TasksPage from "./page";

function jsonResponse(body: unknown, ok = true, status = ok ? 200 : 500) {
  return {
    ok,
    status,
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
    expect(container.textContent).toContain("할 일 추적");
    expect(container.textContent).toContain("위임한 작업");
    expect(container.textContent).toContain("실제 티켓 큐");
    expect(container.textContent).toContain("연결된 티켓 없음");
  });

  it("loads source-linked tickets from the signed task API", async () => {
    const fetchMock = vi.fn(async () => jsonResponse([
      {
        id: "task_public_123",
        title: "보낸 메일 회신 추적",
        status: "in_progress",
        priority: "high",
        source_type: "email",
        source_email_id: "mail_public_456",
        related_thread_id: "thread_public_789",
        updated_at: "2026-05-26T09:00:00.000Z",
      },
    ]));
    vi.stubGlobal("fetch", fetchMock);
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<TasksPage />);
    });
    await flushAsyncWork();

    expect(fetchMock).toHaveBeenCalledWith("/api/tasks", expect.objectContaining({
      headers: expect.objectContaining({ "Content-Type": "application/json" }),
    }));
    expect(container.textContent).toContain("1개 티켓 연결");
    expect(container.textContent).toContain("보낸 메일 회신 추적");
    expect(container.textContent).toContain("mail_public_456");
    expect(container.textContent).toContain("thread_public_789");
  });

  it("distinguishes signed-session authorization failures from generic task API errors", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ detail: "forbidden" }, false, 403)));
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<TasksPage />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("인증된 세션 필요");
    expect(container.textContent).toContain("signed session");
    expect(container.textContent).not.toContain("작업 API 오류");
  });
});
