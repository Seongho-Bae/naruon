/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("lucide-react", () => ({
  Search: () => <svg aria-hidden="true" />,
  Filter: () => <svg aria-hidden="true" />,
  FolderOpen: () => <svg aria-hidden="true" />,
  MoreHorizontal: () => <svg aria-hidden="true" />,
  FileText: () => <svg aria-hidden="true" />,
  User: () => <svg aria-hidden="true" />,
  Clock: () => <svg aria-hidden="true" />,
  AlertCircle: () => <svg aria-hidden="true" />,
  CalendarDays: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  LockKeyhole: () => <svg aria-hidden="true" />,
  Mail: () => <svg aria-hidden="true" />,
  Network: () => <svg aria-hidden="true" />,
  Plus: () => <svg aria-hidden="true" />,
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

    expect(container.textContent).toContain("새 프로젝트");
    expect(container.textContent).toContain("진행 중");
    expect(container.textContent).toContain("제품 개발");
  });
});
