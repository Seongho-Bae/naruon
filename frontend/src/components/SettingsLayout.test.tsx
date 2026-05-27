/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("lucide-react", () => ({
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
  });

  it("renders settings tabs as detail surfaces instead of placeholder dead space", async () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<SettingsLayout />);
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
