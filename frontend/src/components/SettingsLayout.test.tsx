/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("lucide-react", () => ({
  Activity: () => <svg aria-hidden="true" />,
  AlertCircle: () => <svg aria-hidden="true" />,
  Bell: () => <svg aria-hidden="true" />,
  Mail: () => <svg aria-hidden="true" />,
  Monitor: () => <svg aria-hidden="true" />,
  Plus: () => <svg aria-hidden="true" />,
  RefreshCw: () => <svg aria-hidden="true" />,
  Settings: () => <svg aria-hidden="true" />,
  Shield: () => <svg aria-hidden="true" />,
  Smartphone: () => <svg aria-hidden="true" />,
  User: () => <svg aria-hidden="true" />,
}));

import { SettingsLayout } from "./SettingsLayout";

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("SettingsLayout", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  beforeEach(() => {
    localStorage.setItem("naruon_session_token", "signed-runner-session-token");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input) === "/api/runner-config") {
          return jsonResponse({
            workspace_id: "workspace-org-acme",
            configured: true,
            fingerprint: "***abc12345",
            updated_at: "2026-05-27T06:00:00Z",
            connector_manifest: {
              role: "self-hosted_connector",
              network_mode: "outbound_only",
              control_plane_domain: "naruon.net",
              local_protocols: ["imap", "pop3", "smtp", "caldav", "carddav", "webdav"],
              prohibited_roles: ["smtp_server", "imap_server", "mx_host"],
              runner_usage: "ci_smoke_only",
            },
          });
        }
        if (String(input) === "/api/runner-config/rotate" && init?.method === "POST") {
          return jsonResponse({
            workspace_id: "workspace-org-acme",
            registration_token: "nrn_one_time_connector_token",
            connector_manifest: {
              role: "self-hosted_connector",
              network_mode: "outbound_only",
              control_plane_domain: "naruon.net",
              local_protocols: ["imap", "pop3", "smtp", "caldav", "carddav", "webdav"],
              prohibited_roles: ["smtp_server", "imap_server", "mx_host"],
              runner_usage: "ci_smoke_only",
            },
          });
        }
        if (String(input) === "/api/observability/operational-signals") {
          return jsonResponse({
            workspace_id: "workspace-org-acme",
            audit_event: "observability.operational_signals.viewed",
            telemetry: {
              prometheus_metrics_enabled: true,
              otel_traces_enabled: true,
              otel_endpoint_configured: true,
              otel_endpoint_host: "otel-collector:4317",
            },
            connector: {
              workspace_id: "workspace-org-acme",
              registration_state: "registration_configured",
              connection_state: "connected",
              active_connection_count: 1,
              control_plane_domain: "naruon.net",
              network_mode: "outbound_only",
              runner_usage: "ci_smoke_only",
              local_protocols: ["imap", "pop3", "smtp", "caldav", "carddav", "webdav"],
              last_heartbeat_at: "2026-05-27T12:00:00Z",
              last_disconnect_at: null,
              queue_depth_state: "not_reported",
              recent_events: [
                {
                  event_uid: "connector_evt_heartbeat",
                  signal_key: "connector_heartbeat",
                  state_code: "heartbeat",
                  detail_text: "outbound runner heartbeat received",
                  observed_at: "2026-05-27T12:00:00Z",
                },
                {
                  event_uid: "connector_evt_connected",
                  signal_key: "connector_heartbeat",
                  state_code: "connected",
                  detail_text: "outbound runner socket connected",
                  observed_at: "2026-05-27T11:59:00Z",
                },
              ],
            },
            signals: [
              {
                signal_key: "connector_heartbeat",
                display_name: "Connector heartbeat",
                state: "enabled",
                evidence_source: "runner WebSocket manager",
                detail: "Live heartbeat uses active outbound runner sockets.",
                provider_write_executed: false,
              },
              {
                signal_key: "sync_lag",
                display_name: "Sync lag",
                state: "instrumentation_pending",
                evidence_source: "provider adapters",
                detail: "Provider sync lag will be emitted by source-backed connector jobs.",
                provider_write_executed: false,
              },
            ],
          });
        }
        if (String(input) === "/api/calendar/writeback-sources") {
          return jsonResponse([
            {
              source_id: "caldav_src_fastmail_primary",
              provider: "Fastmail",
              protocol: "caldav",
              owner_id: "default",
              organization_id: "org-acme",
              capabilities: ["read", "write", "etag"],
              writeback_enabled: true,
              etag: "etag-caldav-primary",
            },
          ]);
        }
        if (String(input) === "/api/webdav/accounts") {
          return jsonResponse([
            {
              source_id: "webdav_src_primary",
              display_label: "WebDAV source webdav_src_primary",
              writeback_enabled: true,
            },
          ]);
        }
        if (String(input) === "/api/accounts/config" && init?.method === "PUT") {
          const body = JSON.parse(String(init.body));
          return jsonResponse({
            user_id: "default",
            smtp_server: body.smtp_server,
            smtp_port: body.smtp_port,
            smtp_username: body.smtp_username,
            has_smtp_password: false,
            imap_server: body.imap_server,
            imap_port: body.imap_port,
            imap_username: body.imap_username,
            has_imap_password: true,
            pop3_server: body.pop3_server,
            pop3_port: body.pop3_port,
            pop3_username: body.pop3_username,
            has_pop3_password: false,
            oauth_client_id: body.oauth_client_id,
            oauth_redirect_uri: body.oauth_redirect_uri,
            has_oauth_client_secret: true,
          });
        }
        if (String(input) === "/api/accounts/config") {
          return jsonResponse({
            user_id: "default",
            smtp_server: "smtp.example.com",
            smtp_port: 587,
            smtp_username: "sender@example.com",
            has_smtp_password: true,
            imap_server: "imap.example.com",
            imap_port: 993,
            imap_username: "inbox@example.com",
            has_imap_password: true,
            pop3_server: "pop3.example.com",
            pop3_port: 995,
            pop3_username: "archive@example.com",
            has_pop3_password: false,
            oauth_client_id: "oauth-client-id",
            oauth_redirect_uri: "https://naruon.net/oauth/mail/callback",
            has_oauth_client_secret: true,
          });
        }
        return jsonResponse({});
      }),
    );
  });

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it("renders the self-hosted connector manifest and keeps mobile settings tabs reachable", async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<SettingsLayout />);
      await Promise.resolve();
      await Promise.resolve();
    });

    const mobileSettingsNav = container.querySelector('nav[aria-label="설정 섹션"]');
    expect(mobileSettingsNav?.textContent).toContain("개발자");

    const developerButtons = Array.from(container.querySelectorAll("button")).filter((button) => button.textContent?.includes("개발자"));
    await act(async () => {
      developerButtons[0].dispatchEvent(new MouseEvent("click", { bubbles: true }));
      await Promise.resolve();
    });

    expect(fetch).toHaveBeenCalledWith(
      "/api/runner-config",
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer signed-runner-session-token",
        }),
      }),
    );
    expect(fetch).toHaveBeenCalledWith(
      "/api/observability/operational-signals",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer signed-runner-session-token",
        }),
      }),
    );
    const operationalCall = vi.mocked(fetch).mock.calls.find(([input]) => String(input) === "/api/observability/operational-signals");
    expect(operationalCall?.[1]?.headers).not.toHaveProperty("X-User-Id");
    expect(operationalCall?.[1]?.headers).not.toHaveProperty("X-Organization-Id");
    expect(operationalCall?.[1]?.headers).not.toHaveProperty("X-Group-Id");
    expect(operationalCall?.[1]?.headers).not.toHaveProperty("X-Group-Ids");
    expect(operationalCall?.[1]?.headers).not.toHaveProperty("X-User-Role");
    expect(operationalCall?.[1]?.headers).not.toHaveProperty("X-Dev-Auth-Token");
    expect(container.textContent).toContain("Self-hosted connector manifest");
    expect(container.textContent).toContain("Naruon은 이메일 서버가 아닙니다");
    expect(container.textContent).toContain("self-hosted_connector");
    expect(container.textContent).toContain("outbound_only");
    expect(container.textContent).toContain("naruon.net");
    expect(container.textContent).toContain("ci_smoke_only");
    expect(container.textContent).toContain("caldav");
    expect(container.textContent).toContain("webdav");
    expect(container.textContent).toContain("smtp_server");
    expect(container.textContent).toContain("imap_server");
    expect(container.textContent).toContain("mx_host");
    expect(container.textContent).toContain("Connector health & APM signals");
    expect(container.textContent).toContain("observability.operational_signals.viewed");
    expect(container.textContent).toContain("connected");
    expect(container.textContent).toContain("otel-collector:4317");
    expect(container.textContent).toContain("Recent connector signals");
    expect(container.textContent).toContain("connector_evt_heartbeat");
    expect(container.textContent).toContain("outbound runner heartbeat received");
    expect(container.textContent).not.toContain("nrn_registered-token");
    expect(container.textContent).toContain("Connector heartbeat");
    expect(container.textContent).toContain("instrumentation_pending");

    const rotateButton = Array.from(container.querySelectorAll("button")).find((button) => button.textContent?.includes("등록 토큰 회전"));
    expect(rotateButton).toBeTruthy();
    await act(async () => {
      rotateButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      await Promise.resolve();
      await Promise.resolve();
    });

    const rotateCall = vi.mocked(fetch).mock.calls.find(([input, init]) => String(input) === "/api/runner-config/rotate" && init?.method === "POST");
    expect(rotateCall?.[1]?.headers).toMatchObject({
      Authorization: "Bearer signed-runner-session-token",
    });
    expect(rotateCall?.[1]?.headers).not.toHaveProperty("X-User-Id");
    expect(rotateCall?.[1]?.headers).not.toHaveProperty("X-Organization-Id");
    expect(rotateCall?.[1]?.headers).not.toHaveProperty("X-Dev-Auth-Token");
    expect(container.textContent).toContain("One-time connector registration token");
    expect(container.textContent).toContain("nrn_one_time_connector_token");
  });

  it("marks external operational console links with explicit noopener", async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<SettingsLayout />);
      await Promise.resolve();
      await Promise.resolve();
    });

    const developerTab = Array.from(container.querySelectorAll("button")).find(
      (button) => button.textContent === "개발자",
    );
    expect(developerTab).toBeTruthy();
    await act(async () => {
      developerTab?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      await Promise.resolve();
      await Promise.resolve();
    });

    const externalLinks = Array.from(
      container.querySelectorAll<HTMLAnchorElement>('a[target="_blank"]'),
    );
    expect(externalLinks.map((link) => link.textContent)).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Grafana"),
        expect.stringContaining("Keycloak"),
        expect.stringContaining("Loki"),
        expect.stringContaining("Tempo"),
      ]),
    );
    for (const link of externalLinks) {
      expect(link.rel.split(/\s+/).sort()).toEqual(["noopener", "noreferrer"]);
    }
  });

  it("loads and saves source-backed mail account settings without public identity headers or secret replay", async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<SettingsLayout />);
      await Promise.resolve();
      await Promise.resolve();
    });

    const accountButton = Array.from(container.querySelectorAll("button")).find((button) => button.textContent === "연결 계정");
    expect(accountButton).toBeTruthy();
    await act(async () => {
      accountButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(fetch).toHaveBeenCalledWith(
      "/api/accounts/config",
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer signed-runner-session-token",
        }),
      }),
    );
    const configGetCall = vi.mocked(fetch).mock.calls.find(([input, init]) => String(input) === "/api/accounts/config" && init?.method !== "PUT");
    expect(configGetCall?.[1]?.headers).not.toHaveProperty("X-User-Id");
    expect(configGetCall?.[1]?.headers).not.toHaveProperty("X-Organization-Id");
    expect(configGetCall?.[1]?.headers).not.toHaveProperty("X-Group-Id");
    expect(configGetCall?.[1]?.headers).not.toHaveProperty("X-Group-Ids");
    expect(configGetCall?.[1]?.headers).not.toHaveProperty("X-User-Role");
    expect(configGetCall?.[1]?.headers).not.toHaveProperty("X-Dev-Auth-Token");
    const calendarSourcesCall = vi.mocked(fetch).mock.calls.find(([input]) => String(input) === "/api/calendar/writeback-sources");
    const webdavAccountsCall = vi.mocked(fetch).mock.calls.find(([input]) => String(input) === "/api/webdav/accounts");
    expect(calendarSourcesCall?.[1]?.headers).toMatchObject({
      Authorization: "Bearer signed-runner-session-token",
    });
    expect(webdavAccountsCall?.[1]?.headers).toMatchObject({
      Authorization: "Bearer signed-runner-session-token",
    });
    for (const sourceCall of [calendarSourcesCall, webdavAccountsCall]) {
      expect(sourceCall?.[1]?.headers).not.toHaveProperty("X-User-Id");
      expect(sourceCall?.[1]?.headers).not.toHaveProperty("X-Organization-Id");
      expect(sourceCall?.[1]?.headers).not.toHaveProperty("X-Group-Id");
      expect(sourceCall?.[1]?.headers).not.toHaveProperty("X-Group-Ids");
      expect(sourceCall?.[1]?.headers).not.toHaveProperty("X-User-Role");
      expect(sourceCall?.[1]?.headers).not.toHaveProperty("X-Dev-Auth-Token");
    }

    expect(container.textContent).toContain("고객 지정 Provider");
    expect(container.textContent).toContain("smtp.example.com:587");
    expect(container.textContent).toContain("imap.example.com:993");
    expect(container.textContent).toContain("pop3.example.com:995");
    expect(container.textContent).toContain("OAuth 로그인");
    expect(container.textContent).toContain("앱 설정 완료, 사용자 consent 대기");
    expect(container.textContent).toContain("Source readiness");
    expect(container.textContent).toContain("caldav_src_fastmail_primary");
    expect(container.textContent).toContain("webdav_src_primary");
    expect(container.textContent).toContain("WebDAV source webdav_src_primary");
    expect(container.textContent).not.toContain("https://files.example.com/dav");
    expect(container.textContent).not.toContain("files@example.com");
    expect(container.textContent).toContain("writeback intent enabled");
    expect(container.textContent).toContain("저장된 secret 유지");
    expect(container.textContent).toContain("Naruon은 메일함 용량이나 SMTP/IMAP 서버를 제공하지 않습니다");

    const saveButton = Array.from(container.querySelectorAll("button")).find((button) => button.textContent === "계정 설정 저장");
    expect(saveButton).toBeTruthy();
    await act(async () => {
      saveButton?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      await Promise.resolve();
      await Promise.resolve();
    });

    const putCall = vi.mocked(fetch).mock.calls.find(([input, init]) => String(input) === "/api/accounts/config" && init?.method === "PUT");
    expect(putCall).toBeTruthy();
    expect(putCall?.[1]?.headers).not.toHaveProperty("X-User-Id");
    expect(putCall?.[1]?.headers).not.toHaveProperty("X-Organization-Id");
    expect(putCall?.[1]?.headers).not.toHaveProperty("X-Group-Id");
    expect(putCall?.[1]?.headers).not.toHaveProperty("X-Group-Ids");
    expect(putCall?.[1]?.headers).not.toHaveProperty("X-User-Role");
    expect(putCall?.[1]?.headers).not.toHaveProperty("X-Dev-Auth-Token");
    const putBody = JSON.parse(String(putCall?.[1]?.body));
    expect(putBody).toMatchObject({
      smtp_server: "smtp.example.com",
      smtp_port: 587,
      smtp_username: "sender@example.com",
      imap_server: "imap.example.com",
      imap_port: 993,
      imap_username: "inbox@example.com",
      pop3_server: "pop3.example.com",
      pop3_port: 995,
      pop3_username: "archive@example.com",
      oauth_client_id: "oauth-client-id",
      oauth_redirect_uri: "https://naruon.net/oauth/mail/callback",
    });
    expect(putBody).not.toHaveProperty("smtp_password");
    expect(putBody).not.toHaveProperty("imap_password");
    expect(putBody).not.toHaveProperty("pop3_password");
    expect(putBody).not.toHaveProperty("oauth_client_secret");
    expect(container.textContent).toContain("계정 설정을 저장했습니다");
  });

  it("renders settings tabs as detail surfaces instead of placeholder dead space", async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<SettingsLayout />);
      await Promise.resolve();
      await Promise.resolve();
    });

    for (const tabName of ["멤버", "알림", "자동화", "결제"]) {
      const button = Array.from(container.querySelectorAll("button")).find((candidate) => candidate.textContent === tabName);
      expect(button).toBeTruthy();
      await act(async () => {
        button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        await Promise.resolve();
      });
      expect(container.textContent).toContain(`${tabName === "멤버" ? "멤버와 역할" : tabName === "알림" ? "알림 정책" : tabName === "자동화" ? "자동화 규칙" : "결제와 사용량"}`);
      expect(container.textContent).not.toContain("다음 릴리즈");
    }
  });
});
