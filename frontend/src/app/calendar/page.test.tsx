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
  GitBranch: () => <svg aria-hidden="true" />,
  RefreshCw: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  Users: () => <svg aria-hidden="true" />,
}));

import CalendarPage from "./page";

describe("CalendarPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
  });

  it("renders monthly weekly detail coordination candidate and CalDAV writeback workspaces", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<CalendarPage />);
    });

    expect(container.querySelector("h1")?.textContent).toContain("일정 관리");
    expect(container.textContent).toContain("월간 캘린더");
    expect(container.textContent).toContain("주간 캘린더");
    expect(container.textContent).toContain("일정 상세");
    expect(container.textContent).toContain("회의 조율");
    expect(container.textContent).toContain("일정 후보");
    expect(container.textContent).toContain("CalDAV 계정별 writeback 큐");
    expect(container.textContent).toContain("회사 CalDAV");
    expect(container.textContent).toContain("개인 CalDAV");
    expect(container.textContent).toContain("ETag");
    expect(container.textContent).not.toContain("다음 구현 단계");
  });
});
