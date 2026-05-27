/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("lucide-react", () => ({
  CalendarDays: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  Clock: () => <svg aria-hidden="true" />,
  Users: () => <svg aria-hidden="true" />,
  Video: () => <svg aria-hidden="true" />,
  Plus: () => <svg aria-hidden="true" />,
  ChevronLeft: () => <svg aria-hidden="true" />,
  ChevronRight: () => <svg aria-hidden="true" />,
  Settings: () => <svg aria-hidden="true" />,
  X: () => <svg aria-hidden="true" />,
  Paperclip: () => <svg aria-hidden="true" />,
}));

import CalendarPage from "./page";

function jsonResponse(body: unknown, ok = true, status = ok ? 200 : 500) {
  return {
    ok,
    status,
    statusText: ok ? "OK" : "Error",
    json: async () => body,
  } as Response;
}

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

describe("CalendarPage", () => {
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

  it("renders monthly weekly detail coordination candidate and CalDAV writeback workspaces", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<CalendarPage />);
    });

    expect(container.textContent).toContain("새 일정");
    expect(container.textContent).toContain("CalDAV/CardDAV/WebDAV writeback intent");
    expect(container.textContent).not.toContain("뷰는 아직 구현 중입니다");
  });

  it("creates a signed customer-owned calendar writeback intent", async () => {
    localStorage.setItem("naruon_session_token", "signed-calendar-session");
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      expect(String(input)).toBe("/api/calendar/writeback-intent");
      expect(init?.method).toBe("POST");
      expect(init?.headers).toEqual(expect.objectContaining({
        "Content-Type": "application/json",
        Authorization: "Bearer signed-calendar-session",
      }));
      const requestHeaders = init?.headers as Record<string, string>;
      const normalizedHeaderNames = new Set(Object.keys(requestHeaders).map((headerName) => headerName.toLowerCase()));
      for (const publicHeader of [
        "x-user-id",
        "x-organization-id",
        "x-group-id",
        "x-group-ids",
        "x-user-role",
        "x-dev-auth-token",
      ]) {
        expect(normalizedHeaderNames.has(publicHeader)).toBe(false);
      }
      expect(JSON.parse(String(init?.body))).toEqual({
        action: "create",
        summary: "Naruon 일정 후보 writeback intent 점검",
      });
      return jsonResponse({
        workspace_id: "workspace-org-acme",
        target_source_id: "caldav-primary",
        protocol: "caldav",
        writeback_mode: "customer_owned",
        requires_if_match: false,
        if_match: null,
        provenance: {
          created_by: "user-1",
          source_provider: "Customer CalDAV",
          source_protocol: "caldav",
        },
        audit_event: "calendar.writeback_intent.created",
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<CalendarPage />);
    });

    const button = Array.from(container.querySelectorAll("button")).find((node) => node.textContent?.includes("새 일정 intent 점검"));
    expect(button).toBeTruthy();
    await act(async () => {
      button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("customer_owned");
    expect(container.textContent).toContain("caldav");
    expect(container.textContent).toContain("caldav-primary");
    expect(container.textContent).toContain("calendar.writeback_intent.created");
  });

  it("shows a loading state while writeback intent is pending", async () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<CalendarPage />);
    });

    const button = Array.from(container.querySelectorAll("button")).find((node) => node.textContent?.includes("새 일정 intent 점검"));
    await act(async () => {
      button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(container.textContent).toContain("writeback intent 요청 중입니다.");
  });

  it("distinguishes no-source and ETag conflict writeback errors", async () => {
    const responses = [
      jsonResponse({ detail: "No customer-owned writeback source is available" }, false, 422),
      jsonResponse({ detail: "ETag is required for writeback updates" }, false, 409),
    ];
    vi.stubGlobal("fetch", vi.fn(async () => responses.shift() ?? jsonResponse({}, false, 500)));
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<CalendarPage />);
    });

    const createButton = Array.from(container.querySelectorAll("button")).find((node) => node.textContent?.includes("새 일정 intent 점검"));
    await act(async () => {
      createButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    await flushAsyncWork();
    expect(container.textContent).toContain("원본 CalDAV/CardDAV/WebDAV 계정이 없어");

    const updateButton = Array.from(container.querySelectorAll("button")).find((node) => node.textContent?.includes("ETag 업데이트 점검"));
    await act(async () => {
      updateButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    await flushAsyncWork();
    expect(container.textContent).toContain("ETag/If-Match 충돌");
  });
});
