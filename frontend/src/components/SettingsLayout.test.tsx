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
      vi.fn(async (input: RequestInfo | URL) => {
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
