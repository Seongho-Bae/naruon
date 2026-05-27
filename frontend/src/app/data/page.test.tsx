/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("lucide-react", () => ({
  Database: () => <svg aria-hidden="true" />,
  FileArchive: () => <svg aria-hidden="true" />,
  FolderTree: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  HardDrive: () => <svg aria-hidden="true" />,
  FolderOpen: () => <svg aria-hidden="true" />,
  RefreshCw: () => <svg aria-hidden="true" />,
  AlertCircle: () => <svg aria-hidden="true" />,
  FileText: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  Server: () => <svg aria-hidden="true" />,
}));

import DataPage from "./page";

function jsonResponse(body: unknown) {
  return {
    ok: true,
    json: async () => body,
  };
}

function mockWebdavFetch() {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    if (path === "/api/webdav/accounts") {
      return jsonResponse([
        {
          source_id: "webdav_src_primary",
          server_url: "https://webdav.naruon.net",
          username: "demo_user",
          writeback_enabled: true,
        },
      ]);
    }
    if (path === "/api/webdav/folders") {
      return jsonResponse([
        {
          folder_id: 1,
          project_name: "Naruon Roadmap 2026",
          webdav_path: "/Projects/Naruon_Roadmap_2026",
        },
      ]);
    }
    if (path === "/api/webdav/writeback-intent") {
      void init;
      return jsonResponse({
        intent: "writeback",
        source_id: "webdav_src_primary",
        server_url: "https://webdav.naruon.net",
        requires_if_match: true,
        provenance: "server-authoritative",
      });
    }
    if (path === "/api/emails/unique-thread-intent") {
      void init;
      return jsonResponse({
        status: "intent_ready",
        candidates_checked: 2,
        duplicates_found: 2,
        provider_write_executed: false,
        provenance: "server-authoritative",
        audit_event: "email.unique_thread_intent.created",
        thread_updates: [
          {
            candidate_key: "zip-q2-root",
            canonical_thread_id: "thread-q2-root",
            dedupe_key: "q2-root@example.com",
            match_reason: "message_id",
            existing_message_id: "q2-root@example.com",
          },
          {
            candidate_key: "forwarded-copy",
            canonical_thread_id: "thread-q2-root",
            dedupe_key: "sha256:duplicate",
            match_reason: "fingerprint",
            existing_message_id: "q2-root@example.com",
          },
        ],
      });
    }
    throw new Error(`Unhandled fetch: ${path}`);
  });
}

describe("DataPage", () => {
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

  it("renders document repository ingestion embeddings quality and WebDAV writeback details", async () => {
    vi.stubGlobal("fetch", mockWebdavFetch());
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<DataPage />);
    });

    expect(container.querySelector("h1")?.textContent).toContain("데이터와 파일");
    expect(container.textContent).toContain("저장소");
    expect(container.textContent).toContain("데이터와 파일");
    expect(container.textContent).toContain("WebDAV 원본");
    expect(container.textContent).toContain("로컬 캐시");
    expect(container.textContent).toContain("WebDAV writeback intent 승인");
  });

  it("creates a signed customer-owned WebDAV writeback intent", async () => {
    localStorage.setItem("naruon_session_token", "signed-webdav-session");
    const fetchMock = mockWebdavFetch();
    vi.stubGlobal("fetch", fetchMock);
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<DataPage />);
    });

    const button = Array.from(container.querySelectorAll("button")).find((candidate) =>
      candidate.textContent?.includes("WebDAV intent 승인 점검"),
    );
    expect(button).toBeDefined();

    await act(async () => {
      button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    const writebackCall = fetchMock.mock.calls.find(([input]) => String(input) === "/api/webdav/writeback-intent");
    expect(writebackCall).toBeDefined();
    const [, init] = writebackCall ?? [];
    expect(init?.method).toBe("POST");
    const headerEntries =
      init?.headers instanceof Headers
        ? Array.from(init.headers.entries())
        : Object.entries((init?.headers as Record<string, string>) ?? {});
    const requestHeaders = Object.fromEntries(
      headerEntries.map(([key, value]) => [key.toLowerCase(), String(value)]),
    );
    expect(requestHeaders).toEqual(expect.objectContaining({
      authorization: "Bearer signed-webdav-session",
      "content-type": "application/json",
    }));
    for (const publicHeader of [
      "x-user-id",
      "x-organization-id",
      "x-group-id",
      "x-group-ids",
      "x-user-role",
      "x-dev-auth-token",
    ]) {
      expect(requestHeaders[publicHeader]).toBeUndefined();
    }
    expect(JSON.parse(String(init?.body))).toEqual({
      target_source_id: "webdav_src_primary",
    });
    expect(container.textContent).toContain("server-authoritative");
    expect(container.textContent).toContain("https://webdav.naruon.net");
  });

  it("creates a signed unique email thread intent without public identity headers", async () => {
    localStorage.setItem("naruon_session_token", "signed-email-dedupe-session");
    const fetchMock = mockWebdavFetch();
    vi.stubGlobal("fetch", fetchMock);
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<DataPage />);
    });

    const button = Array.from(container.querySelectorAll("button")).find((candidate) =>
      candidate.textContent?.includes("중복 메일 thread intent 점검"),
    );
    expect(button).toBeDefined();

    await act(async () => {
      button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    const intentCall = fetchMock.mock.calls.find(([input]) => String(input) === "/api/emails/unique-thread-intent");
    expect(intentCall).toBeDefined();
    const [, init] = intentCall ?? [];
    expect(init?.method).toBe("POST");
    const headerEntries =
      init?.headers instanceof Headers
        ? Array.from(init.headers.entries())
        : Object.entries((init?.headers as Record<string, string>) ?? {});
    const requestHeaders = Object.fromEntries(
      headerEntries.map(([key, value]) => [key.toLowerCase(), String(value)]),
    );
    expect(requestHeaders).toEqual(expect.objectContaining({
      authorization: "Bearer signed-email-dedupe-session",
      "content-type": "application/json",
    }));
    for (const publicHeader of [
      "x-user-id",
      "x-organization-id",
      "x-group-id",
      "x-group-ids",
      "x-user-role",
      "x-dev-auth-token",
    ]) {
      expect(requestHeaders[publicHeader]).toBeUndefined();
    }
    const requestBody = JSON.parse(String(init?.body));
    expect(requestBody.candidates).toHaveLength(2);
    expect(requestBody.candidates[0]).toEqual(expect.objectContaining({
      candidate_key: "zip-q2-root",
      message_id: "q2-root@example.com",
    }));
    expect(container.textContent).toContain("email.unique_thread_intent.created");
    expect(container.textContent).toContain("thread-q2-root");
    expect(container.textContent).toContain("provider_write_executed=false");
  });
});
