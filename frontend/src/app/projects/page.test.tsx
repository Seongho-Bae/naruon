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
    if (root) act(() => root.unmount());
    root = null;
    container?.remove();
    container = null;
  });

  it("renders detailed project workspace sections for sidebar deep links and north-star integrations", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<ProjectsPage />);
    });

    expect(container.querySelector('h1')?.textContent).toContain("프로젝트 워크스페이스");
    expect(container.querySelector('section#launch[aria-label="런칭 프로젝트"]')).not.toBeNull();
    expect(container.querySelector('section#vendor[aria-label="벤더 관리"]')).not.toBeNull();
    expect(container.querySelector('section#marketing[aria-label="마케팅 캠페인"]')).not.toBeNull();
    expect(container.textContent).toContain("CalDAV/CardDAV/WebDAV");
    expect(container.textContent).toContain("self-hosted connector");
    expect(container.textContent).toContain("Keycloak");
    expect(container.textContent).toContain("Traefik");
    expect(container.textContent).toContain("OpenTelemetry");
    expect(container.textContent).toContain("RBAC/ABAC");
    expect(container.textContent).not.toContain("준비 중");
    expect(container.querySelector<HTMLAnchorElement>('a[href="/#mobile-calendar"]')?.textContent).toContain("일정 후보 열기");
  });
});
