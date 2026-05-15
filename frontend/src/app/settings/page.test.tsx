/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

const apiClientMock = vi.hoisted(() => ({
  getCurrentUserId: vi.fn(),
  getCurrentOrganizationId: vi.fn(),
  canManageWorkspaceSettings: vi.fn(),
  getSessionClaims: vi.fn(),
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}));

vi.mock("@/lib/api-client", () => ({
  apiClient: apiClientMock,
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
}));

vi.mock("@/components/ui/input", () => ({
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
}));

vi.mock("@/components/ui/tabs", () => ({
  Tabs: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabsList: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabsTrigger: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
  TabsContent: ({ children }: { children: React.ReactNode }) => <section>{children}</section>,
}));

vi.mock("lucide-react", () => {
  const Icon = () => <svg aria-hidden="true" />;
  return {
    Activity: Icon,
    AlertCircle: Icon,
    CheckCircle2: Icon,
    Key: Icon,
    Mail: Icon,
    Server: Icon,
    Settings: Icon,
    Shield: Icon,
  };
});

import SettingsPage from "./page";

async function flushAsyncWork() {
  for (let index = 0; index < 5; index += 1) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

describe("SettingsPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    vi.clearAllMocks();
  });

  it("hides organization admin tabs and skips admin API fetches for member claims", async () => {
    apiClientMock.getCurrentUserId.mockReturnValue("member-1");
    apiClientMock.getCurrentOrganizationId.mockReturnValue("org-acme");
    apiClientMock.canManageWorkspaceSettings.mockReturnValue(false);
    apiClientMock.getSessionClaims.mockReturnValue({
      sub: "member-1",
      roles: ["member"],
      organization_id: "org-acme",
    });
    apiClientMock.get.mockImplementation(async (endpoint: string) => {
      if (endpoint === "/api/mailbox-accounts") {
        return {
          items: [],
        };
      }
      if (endpoint.startsWith("/api/config?user_id=")) {
        return {
          user_id: "member-1",
          smtp_server: null,
          smtp_port: null,
          smtp_username: null,
          smtp_password: null,
          imap_server: null,
          imap_port: null,
          imap_username: null,
          imap_password: null,
        };
      }
      throw new Error(`Unexpected endpoint: ${endpoint}`);
    });

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<SettingsPage />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("개인 이메일 계정");
    expect(container.textContent).toContain("연결된 메일 계정");
    expect(container.textContent).not.toContain("워크스페이스 BYOK (관리자)");
    expect(container.textContent).not.toContain("Self-hosted Runner (관리자)");
    expect(apiClientMock.get).toHaveBeenCalledWith("/api/mailbox-accounts");
    expect(apiClientMock.get).not.toHaveBeenCalledWith("/api/llm-providers");
    expect(apiClientMock.get).not.toHaveBeenCalledWith("/api/runner-config");
  });

  it("shows organization admin tabs for organization_admin claims", async () => {
    apiClientMock.getCurrentUserId.mockReturnValue("admin-1");
    apiClientMock.getCurrentOrganizationId.mockReturnValue("org-acme");
    apiClientMock.canManageWorkspaceSettings.mockReturnValue(true);
    apiClientMock.getSessionClaims.mockReturnValue({
      sub: "admin-1",
      roles: ["organization_admin"],
      organization_id: "org-acme",
    });
    apiClientMock.get.mockImplementation(async (endpoint: string) => {
      if (endpoint === "/api/mailbox-accounts") {
        return {
          items: [
            {
              id: 1,
              user_id: "admin-1",
              email_address: "alpha@example.com",
              display_name: "Alpha",
              provider: "custom",
              is_default_reply: true,
              is_active: true,
              smtp_server: "smtp.example.com",
              smtp_port: 587,
              smtp_username: "alpha@example.com",
              smtp_password_set: true,
              imap_server: "imap.example.com",
              imap_port: 993,
              imap_username: "alpha@example.com",
              imap_password_set: true,
              pop3_server: "pop.example.com",
              pop3_port: 995,
              pop3_username: "alpha@example.com",
              pop3_password_set: true,
            },
          ],
        };
      }
      if (endpoint === "/api/llm-providers") return [];
      if (endpoint === "/api/runner-config") {
        return {
          workspace_id: "workspace-org-acme",
          configured: false,
          fingerprint: null,
          updated_at: null,
        };
      }
      if (endpoint.startsWith("/api/config?user_id=")) {
        return {
          user_id: "admin-1",
          smtp_server: null,
          smtp_port: null,
          smtp_username: null,
          smtp_password: null,
          imap_server: null,
          imap_port: null,
          imap_username: null,
          imap_password: null,
        };
      }
      throw new Error(`Unexpected endpoint: ${endpoint}`);
    });

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<SettingsPage />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("워크스페이스 BYOK (관리자)");
    expect(container.textContent).toContain("Self-hosted Runner (관리자)");
    expect(container.textContent).toContain("alpha@example.com");
    expect(container.textContent).toContain("기본 회신 계정");
    expect(container.textContent).toContain("POP3");
    expect(apiClientMock.get).toHaveBeenCalledWith("/api/mailbox-accounts");
    expect(apiClientMock.get).toHaveBeenCalledWith("/api/llm-providers");
    expect(apiClientMock.get).toHaveBeenCalledWith("/api/runner-config");
  });
});
