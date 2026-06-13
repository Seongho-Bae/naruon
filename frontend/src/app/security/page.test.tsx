/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("lucide-react", () => ({
  AlertOctagon: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  Database: () => <svg aria-hidden="true" />,
  Lock: () => <svg aria-hidden="true" />,
  RefreshCw: () => <svg aria-hidden="true" />,
  ScrollText: () => <svg aria-hidden="true" />,
  Share2: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  XCircle: () => <svg aria-hidden="true" />,
}));

import SecurityPage from "./page";

function jsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    statusText: "OK",
    json: async () => body,
  };
}

const securitySurface = {
  workspace_id: "workspace-org-acme",
  organization_id: "org-acme",
  audit_event: "security.access_surface.viewed",
  viewer: {
    user_id: "admin",
    role: "tenant_admin",
    organization_id: "org-acme",
    group_ids: ["group-security"],
    workspace_id: "workspace-org-acme",
  },
  sources: [
    {
      source_id: "webdav_src_primary",
      source_type: "webdav_repository",
      source_label: "WebDAV repository",
      source_host: "files.acme.example",
      owner_id: "owner",
      organization_id: "org-acme",
      workspace_id: "workspace-org-acme",
      capabilities: ["read", "write", "etag"],
      writeback_enabled: true,
      provider_write_executed: false,
      last_observed_at: "2026-05-28T04:00:00Z",
      policy_decision: {
        decision_uid: "policy:webdav_src_primary",
        resource_label: "WebDAV repository",
        resource_type: "webdav_repository",
        allowed: true,
        reason: "allowed",
        evidence_source: "webdav_accounts",
      },
    },
  ],
  connector_events: [
    {
      event_uid: "connector_evt_heartbeat",
      signal_key: "connector_heartbeat",
      state_code: "heartbeat",
      detail_text: "outbound connector heartbeat",
      observed_at: "2026-05-28T04:00:00Z",
    },
  ],
  durable_audit_events: [
    {
      event_uid: "audit_evt_provider_update",
      actor_user_id: "admin",
      actor_role: "tenant_admin",
      organization_id: "org-acme",
      workspace_id: "workspace-org-acme",
      event_action: "update",
      resource_type: "llm_provider",
      resource_uid: "llm_provider:provider_primary",
      evidence_source: "api.llm_providers",
      detail_text: "Updated provider configuration",
      observed_at: "2026-05-28T04:02:00Z",
    },
  ],
  policy_decisions: [
    {
      decision_uid: "policy:webdav_src_primary",
      resource_label: "WebDAV repository",
      resource_type: "webdav_repository",
      allowed: true,
      reason: "allowed",
      evidence_source: "webdav_accounts",
    },
    {
      decision_uid: "policy:cross-organization-deny",
      resource_label: "Cross-organization provider secret",
      resource_type: "provider_secret",
      allowed: false,
      reason: "organization_denied",
      evidence_source: "access_policy.evaluate_access",
    },
  ],
  external_share_reviews: [
    {
      review_uid: "share:webdav_src_primary",
      source_id: "webdav_src_primary",
      source_type: "webdav_repository",
      review_label: "WebDAV repository writeback boundary",
      exposure_level: "external_writeback",
      decision_reason: "allowed",
      provider_write_executed: false,
    },
  ],
  policy_order: [
    {
      step_key: "signed_session",
      display_name: "Signed session identity",
      evidence_source: "api.auth.get_auth_context",
    },
    {
      step_key: "rbac",
      display_name: "RBAC allow after ABAC denies",
      evidence_source: "services.access_policy.evaluate_access",
    },
  ],
};

function mockSecurityFetch() {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    void init;
    if (String(input) === "/api/security/access-surface") {
      return jsonResponse(securitySurface);
    }
    throw new Error(`Unhandled fetch: ${String(input)}`);
  });
}

async function renderSecurityPage() {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => {
    root.render(<SecurityPage />);
    await Promise.resolve();
    await Promise.resolve();
  });
  return { container, root };
}

describe("SecurityPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
    localStorage.clear();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("fetches signed security governance and renders source-backed access data", async () => {
    const fetchMock = mockSecurityFetch();
    vi.stubGlobal("fetch", fetchMock);

    ({ container, root } = await renderSecurityPage());

    expect(container.querySelector("h1")?.textContent).toContain("보안과 관리자");
    expect(container.textContent).toContain("Source-linked RBAC / ABAC");
    expect(container.textContent).toContain("webdav_src_primary");
    expect(container.textContent).toContain("files.acme.example");
    expect(container.textContent).not.toContain("곧 제공됩니다");
    expect(container.textContent).not.toContain("비정상 로그인 시도");

    const accessCall = fetchMock.mock.calls.find(([input]) => String(input) === "/api/security/access-surface");
    expect(accessCall).toBeDefined();
    const [, init] = accessCall ?? [];
    const headerEntries =
      init?.headers instanceof Headers
        ? Array.from(init.headers.entries())
        : Object.entries((init?.headers as Record<string, string>) ?? {});
    const requestHeaders = Object.fromEntries(
      headerEntries.map(([key, value]) => [key.toLowerCase(), String(value)]),
    );
    expect(requestHeaders.authorization).toBeUndefined();
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
  });

  it("renders audit sharing and policy tabs without inert placeholders", async () => {
    vi.stubGlobal("fetch", mockSecurityFetch());
    ({ container, root } = await renderSecurityPage());

    for (const tabName of ["감사 로그", "외부 공유", "정책"]) {
      const tab = Array.from(container.querySelectorAll("button")).find((button) =>
        button.textContent?.includes(tabName),
      );
      expect(tab).toBeDefined();
      await act(async () => {
        tab?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      });
      expect(container.textContent).not.toContain("곧 제공됩니다");
      if (tabName === "감사 로그") {
        expect(container.textContent).toContain("Durable audit evidence");
        expect(container.textContent).toContain("audit_evt_provider_update");
        expect(container.textContent).toContain("llm_provider:provider_primary");
        expect(container.textContent).toContain("connector_evt_heartbeat");
      }
      if (tabName === "외부 공유") {
        expect(container.textContent).toContain("WebDAV repository writeback boundary");
      }
      if (tabName === "정책") {
        expect(container.textContent).toContain("Deny-first policy order");
        expect(container.textContent).toContain("RBAC allow after ABAC denies");
      }
    }
  });
});
