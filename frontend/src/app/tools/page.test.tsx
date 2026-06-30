/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import ToolsPage from "./page";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/tools",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("lucide-react", () => ({
  Activity: () => <svg aria-hidden="true" />,
  AlertCircle: () => <svg aria-hidden="true" />,
  Loader2: () => <svg aria-hidden="true" />,
  Bell: () => <svg aria-hidden="true" />,
  Bot: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  Cpu: () => <svg aria-hidden="true" />,
  Mail: () => <svg aria-hidden="true" />,
  Monitor: () => <svg aria-hidden="true" />,
  Network: () => <svg aria-hidden="true" />,
  Plus: () => <svg aria-hidden="true" />,
  RefreshCw: () => <svg aria-hidden="true" />,
  Settings: () => <svg aria-hidden="true" />,
  Shield: () => <svg aria-hidden="true" />,
  Smartphone: () => <svg aria-hidden="true" />,
  User: () => <svg aria-hidden="true" />,
  Search: () => <svg aria-hidden="true" />,
  X: () => <svg aria-hidden="true" />,
  Inbox: () => <svg aria-hidden="true" />,
  Star: () => <svg aria-hidden="true" />,
  Send: () => <svg aria-hidden="true" />,
  CalendarDays: () => <svg aria-hidden="true" />,
  FolderDot: () => <svg aria-hidden="true" />,
  BarChart3: () => <svg aria-hidden="true" />,
  CheckSquare: () => <svg aria-hidden="true" />,
  FileText: () => <svg aria-hidden="true" />,
  HelpCircle: () => <svg aria-hidden="true" />,
  Home: () => <svg aria-hidden="true" />,
  MessageSquare: () => <svg aria-hidden="true" />,
  MoreHorizontal: () => <svg aria-hidden="true" />,
  Settings2: () => <svg aria-hidden="true" />,
  Users: () => <svg aria-hidden="true" />,
  Wallet: () => <svg aria-hidden="true" />,
  ArrowRight: () => <svg aria-hidden="true" />,
  Briefcase: () => <svg aria-hidden="true" />,
  Sparkles: () => <svg aria-hidden="true" />,
  Database: () => <svg aria-hidden="true" />,
  Lock: () => <svg aria-hidden="true" />,
  SlidersHorizontal: () => <svg aria-hidden="true" />,
  ChevronDown: () => <svg aria-hidden="true" />,
  Wrench: () => <svg aria-hidden="true" />,
  LogOut: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  PenLine: () => <svg aria-hidden="true" />,
  Menu: () => <svg aria-hidden="true" />,
  UserCircle: () => <svg aria-hidden="true" />,
}));

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

describe("ToolsPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    vi.unstubAllGlobals();
  });

  it("renders tools correctly with category", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse([
        { name: "테스트 도구", description: "설명입니다.", category: "테스트 카테고리" },
      ])),
    );

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<ToolsPage />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("테스트 도구");
    expect(container.textContent).toContain("설명입니다.");
    expect(container.textContent).toContain("테스트 카테고리");
  });
});
