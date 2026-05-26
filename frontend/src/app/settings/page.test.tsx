/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

const apiClientMock = vi.hoisted(() => ({
  get: vi.fn(async (path: string) => {
    if (path === "/api/auth/context") return { user_id: "user-default" };
    if (path.startsWith("/api/config")) {
      return {
        user_id: "user-default",
        smtp_server: null,
        smtp_port: 587,
        smtp_username: null,
        smtp_password: null,
        imap_server: null,
        imap_port: 993,
        imap_username: null,
        imap_password: null,
      };
    }
    if (path === "/api/llm-providers") return [];
    if (path === "/api/runner-config") {
      return {
        workspace_id: "default-workspace",
        configured: false,
        fingerprint: null,
        updated_at: null,
      };
    }
    return {};
  }),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}));

vi.mock("@/lib/api-client", () => ({
  apiClient: apiClientMock,
}));

vi.mock("lucide-react", () => ({
  Bell: () => <svg aria-hidden="true" />,
  Briefcase: () => <svg aria-hidden="true" />,
  CalendarDays: () => <svg aria-hidden="true" />,
  Activity: () => <svg aria-hidden="true" />,
  AlertCircle: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  Database: () => <svg aria-hidden="true" />,
  Edit3: () => <svg aria-hidden="true" />,
  FileText: () => <svg aria-hidden="true" />,
  FolderOpen: () => <svg aria-hidden="true" />,
  HelpCircle: () => <svg aria-hidden="true" />,
  Home: () => <svg aria-hidden="true" />,
  Inbox: () => <svg aria-hidden="true" />,
  Key: () => <svg aria-hidden="true" />,
  Mail: () => <svg aria-hidden="true" />,
  Menu: () => <svg aria-hidden="true" />,
  MoreHorizontal: () => <svg aria-hidden="true" />,
  Network: () => <svg aria-hidden="true" />,
  PenLine: () => <svg aria-hidden="true" />,
  Search: () => <svg aria-hidden="true" />,
  Send: () => <svg aria-hidden="true" />,
  Server: () => <svg aria-hidden="true" />,
  Settings: () => <svg aria-hidden="true" />,
  Shield: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  Sparkles: () => <svg aria-hidden="true" />,
  Star: () => <svg aria-hidden="true" />,
  Target: () => <svg aria-hidden="true" />,
  TrendingUp: () => <svg aria-hidden="true" />,
  UserCircle: () => <svg aria-hidden="true" />,
}));

import { DashboardLayout } from "@/components/DashboardLayout";
import SettingsPage from "./page";

async function flushAsyncWork() {
  for (let index = 0; index < 4; index += 1) {
    await act(async () => {
      await Promise.resolve();
      vi.runOnlyPendingTimers();
      await Promise.resolve();
    });
  }
}

describe("SettingsPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
    apiClientMock.get.mockClear();
    vi.useRealTimers();
  });

  it("renders branded scrollable settings controls with persistent account labels", async () => {
    vi.useFakeTimers();
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<SettingsPage />);
    });
    await flushAsyncWork();

    const pageShell = container.querySelector<HTMLElement>('[data-testid="settings-page-scroll"]');
    const tabList = container.querySelector<HTMLElement>('[data-testid="settings-tab-list"]');
    const cards = Array.from(container.querySelectorAll<HTMLElement>('[data-testid="settings-card"]'));

    expect(pageShell).not.toBeNull();
    expect(pageShell?.className).toContain("overflow-y-auto");
    expect(pageShell?.className).toContain("max-h-full");
    expect(tabList).not.toBeNull();
    expect(tabList?.className).toContain("h-auto");
    expect(tabList?.className).toContain("overflow-x-auto");
    expect(cards.length).toBeGreaterThanOrEqual(1);
    for (const card of cards) {
      expect(card.className).toContain("bg-card");
      expect(card.className).not.toContain("bg-white");
    }

    for (const label of [
      "SMTP 서버",
      "SMTP 포트",
      "SMTP 사용자명",
      "SMTP 비밀번호 또는 앱 비밀번호",
      "IMAP 서버",
      "IMAP 포트",
      "IMAP 사용자명",
      "IMAP 비밀번호 또는 앱 비밀번호",
    ]) {
      expect(container.textContent).toContain(label);
    }
  });

  it("keeps settings scrollable inside the DashboardLayout content frame", async () => {
    vi.useFakeTimers();
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(
        <DashboardLayout>
          <SettingsPage />
        </DashboardLayout>,
      );
    });
    await flushAsyncWork();

    const mainContent = container.querySelector<HTMLElement>("main#main-content");
    const pageShell = mainContent?.querySelector<HTMLElement>(
      '[data-testid="settings-page-scroll"]',
    );

    expect(mainContent).not.toBeNull();
    expect(mainContent?.className).toContain("overflow-hidden");
    expect(pageShell).not.toBeNull();
    expect(pageShell?.className).toContain("max-h-full");
    expect(pageShell?.className).toContain("overflow-y-auto");
  });
});
