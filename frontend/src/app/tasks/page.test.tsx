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

  it("updates ticket status through the signed task API", async () => {
    localStorage.setItem("naruon_session_token", "signed.task.status");
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/tasks/task_public_123" && init?.method === "PATCH") {
        expect(init.headers).toEqual(expect.objectContaining({
          Authorization: "Bearer signed.task.status",
          "Content-Type": "application/json",
        }));
        expect(JSON.parse(String(init.body))).toEqual({ status: "done" });
        return jsonResponse({
          id: "task_public_123",
          title: "보낸 메일 회신 추적",
          status: "done",
          priority: "high",
          source_type: "email",
          source_email_id: "mail_public_456",
          related_thread_id: "thread_public_789",
          updated_at: "2026-05-26T10:00:00.000Z",
        });
      }
      return jsonResponse([
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

    const doneButton = container.querySelector<HTMLButtonElement>('button[aria-label="보낸 메일 회신 추적 상태를 완료로 변경"]');
    expect(doneButton).not.toBeNull();
    await act(async () => {
      doneButton?.click();
    });
    await flushAsyncWork();

    expect(fetchMock).toHaveBeenCalledWith("/api/tasks/task_public_123", expect.objectContaining({
      method: "PATCH",
    }));
    expect(container.textContent).toContain("보낸 메일 회신 추적 상태를 완료로 변경했습니다.");
    expect(doneButton?.getAttribute("aria-pressed")).toBe("true");
  });

  it("creates self-sent knowledge WebDAV materialization intent with signed headers", async () => {
    localStorage.setItem("naruon_session_token", "signed.knowledge.intent");
    const publicIdentityHeaders = [
      "x-user-id",
      "x-organization-id",
      "x-group-id",
      "x-group-ids",
      "x-user-role",
      "x-dev-auth-token",
    ];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/webdav/knowledge-materialization-intent") {
        const headers = init?.headers as Record<string, string>;
        expect(init?.method).toBe("POST");
        expect(headers.Authorization).toBe("Bearer signed.knowledge.intent");
        expect(headers["Content-Type"]).toBe("application/json");
        for (const headerName of publicIdentityHeaders) {
          expect(Object.keys(headers).some((key) => key.toLowerCase() === headerName)).toBe(false);
        }
        expect(JSON.parse(String(init?.body))).toEqual({ source_task_id: "task-self-knowledge" });
        return jsonResponse({
          intent: "knowledge_materialization",
          status: "intent_ready",
          task_id: "task-self-knowledge",
          source_type: "self_sent_knowledge",
          source_email_id: "<self-note@example.com>",
          source_thread_id: "thread-self-note",
          source_id: "webdav_src_primary",
          server_url: "https://webdav.naruon.net",
          target_path: "/Naruon/Notes/task-self-knowledge.md",
          requires_if_match: true,
          provenance: "server-authoritative",
          provider_write_executed: false,
          audit_event: "webdav.self_sent_knowledge_intent.created",
        });
      }
      return jsonResponse([
        {
          id: "task-self-knowledge",
          title: "나에게 보낸 지식 메모 정리",
          status: "open",
          priority: "normal",
          source_type: "self_sent_knowledge",
          source_email_id: "<self-note@example.com>",
          related_thread_id: "thread-self-note",
          updated_at: "2026-05-26T09:00:00.000Z",
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

    const intentButton = container.querySelector<HTMLButtonElement>(
      'button[aria-label="나에게 보낸 지식 메모 정리 WebDAV 지식 노트 intent 생성"]',
    );
    expect(intentButton).not.toBeNull();
    await act(async () => {
      intentButton?.click();
    });
    await flushAsyncWork();

    expect(fetchMock).toHaveBeenCalledWith("/api/webdav/knowledge-materialization-intent", expect.objectContaining({
      method: "POST",
    }));
    expect(container.textContent).toContain("/Naruon/Notes/task-self-knowledge.md");
    expect(container.textContent).toContain("https://webdav.naruon.net");
    expect(container.textContent).toContain("provider_write_executed=false");
    expect(container.textContent).toContain("webdav.self_sent_knowledge_intent.created");
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
