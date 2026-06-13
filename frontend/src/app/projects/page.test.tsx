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
  FolderOpen: () => <svg aria-hidden="true" />,
  ListChecks: () => <svg aria-hidden="true" />,
  Search: () => <svg aria-hidden="true" />,
  User: () => <svg aria-hidden="true" />,
}));

import ProjectsPage from "./page";

function jsonResponse(body: unknown, ok = true, status = ok ? 200 : 500) {
  return Promise.resolve({
    ok,
    status,
    statusText: ok ? "OK" : "Server Error",
    json: () => Promise.resolve(body),
  } as Response);
}

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("ProjectsPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("loads project folders and ticket tasks through signed APIs", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const headers = new Headers(init?.headers);
      expect(headers.get("Authorization")).toBeNull();
      expect(headers.get("X-User-Id")).toBeNull();
      expect(headers.get("X-Organization-Id")).toBeNull();

      const path = String(input);
      if (path === "/auth/session") {
        return jsonResponse({
          authenticated: true,
          claims: {
            userId: "alice",
            organizationId: "org-acme",
            workspaceId: "workspace-org-acme",
          },
        });
      }
      if (path === "/api/webdav/folders") {
        return jsonResponse([
          {
            folder_uid: "webdav_folder_roadmap",
            project_name: "Naruon Roadmap 2026",
            webdav_path: "/Projects/Naruon_Roadmap_2026",
            owner_user_id: "alice",
            organization_id: "org-acme",
          },
          {
            folder_uid: "webdav_folder_rival",
            project_name: "Rival Project",
            webdav_path: "/Projects/Rival_Project",
            owner_user_id: "mallory",
            organization_id: "org-rival",
          },
        ]);
      }
      if (path === "/api/tasks") {
        return jsonResponse([
          {
            id: "task-q2-owner",
            title: "리소스 배정 검토 회의",
            status: "blocked",
            priority: "urgent",
            source_type: "email",
            source_email_id: "<q2@example.com>",
            related_thread_id: "thread-q2",
            created_at: "2026-05-19T00:00:00Z",
            updated_at: "2026-05-21T00:00:00Z",
          },
          {
            id: "task-webdav-evidence",
            title: "첨부파일 WebDAV 폴더 정리",
            status: "done",
            priority: "low",
            source_type: "webdav",
            source_email_id: "<q2@example.com>",
            related_thread_id: "thread-q2",
            created_at: "2026-05-19T00:00:00Z",
            updated_at: "2026-05-24T00:00:00Z",
          },
        ]);
      }
      return jsonResponse({}, false, 404);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<ProjectsPage />);
    });
    await flushAsyncWork();

    expect(fetchMock).toHaveBeenCalledWith("/api/webdav/folders", expect.objectContaining({ headers: expect.any(Object) }));
    expect(fetchMock).toHaveBeenCalledWith("/api/tasks", expect.objectContaining({ headers: expect.any(Object) }));
    expect(container.textContent).toContain("Naruon Roadmap 2026");
    expect(container.textContent).not.toContain("Rival Project");
    expect(container.textContent).not.toContain("webdav_folder_roadmap");
    expect(container.textContent).toContain("provider_write_executed=false");
    expect(container.textContent).toContain("리소스 배정 검토 회의");
    expect(container.textContent).toContain("순차 DB id는 화면에 노출하지 않습니다");
    expect(container.textContent).not.toContain("Naruon 2.0 런칭");
  });

  it("renders an actionable fallback when project evidence fails", async () => {
    vi.stubGlobal("fetch", vi.fn(() => jsonResponse({ detail: "failed" }, false, 500)));

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<ProjectsPage />);
    });
    await flushAsyncWork();

    expect(container.querySelector('[role="alert"]')?.textContent).toContain("/api/webdav/folders");
    expect(
      Array.from(container.querySelectorAll('a[href="/data"]')).some((link) => link.textContent?.includes("Data evidence")),
    ).toBe(true);
    expect(container.textContent).toContain("Source-linked 작업 Backlog");
  });
});
