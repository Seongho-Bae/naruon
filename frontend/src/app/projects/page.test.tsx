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
  FolderOpen: () => <svg aria-hidden="true" />,
  LockKeyhole: () => <svg aria-hidden="true" />,
  Mail: () => <svg aria-hidden="true" />,
  Network: () => <svg aria-hidden="true" />,
  ServerCog: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
}));

import ProjectsPage from "./page";

describe("ProjectsPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
  });

  it("renders project execution surfaces with decision logs and source boundaries", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<ProjectsPage />);
    });

    expect(container.querySelector("h1")?.textContent).toContain("프로젝트 워크스페이스");
    expect(container.querySelector('[aria-label="런칭 프로젝트"]')?.textContent).toContain("CalDAV 일정 writeback 후보");
    expect(container.querySelector('[aria-label="벤더 관리"]')?.textContent).toContain("RBAC/ABAC deny 우선 정책");
    expect(container.querySelector('[aria-label="프로젝트 상세 작업"]')?.textContent).toContain("의사결정 로그");
    expect(container.querySelector('[aria-label="프로젝트 상세 작업"]')?.textContent).toContain("산출물 provenance");
    expect(container.textContent).toContain("self-hosted connector");
    expect(container.textContent).toContain("ETag/If-Match");
    expect(container.textContent).toContain("writeback intent");
  });
});
