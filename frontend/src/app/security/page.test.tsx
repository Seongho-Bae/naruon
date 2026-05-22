/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("lucide-react", () => ({
  KeyRound: () => <svg aria-hidden="true" />,
  LockKeyhole: () => <svg aria-hidden="true" />,
  Route: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  Users: () => <svg aria-hidden="true" />,
}));

import SecurityPage from "./page";

describe("SecurityPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
  });

  it("renders security dashboard access audit sharing and policy governance screens", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<SecurityPage />);
    });

    expect(container.querySelector("h1")?.textContent).toContain("보안과 관리자");
    expect(container.textContent).toContain("보안 대시보드");
    expect(container.textContent).toContain("접근 권한");
    expect(container.textContent).toContain("감사 로그");
    expect(container.textContent).toContain("외부 공유");
    expect(container.textContent).toContain("정책");
    expect(container.textContent).toContain("platform_admin");
    expect(container.textContent).toContain("customer policy deny");
    expect(container.textContent).toContain("Keycloak");
    expect(container.textContent).toContain("Casdoor");
    expect(container.textContent).toContain("Traefik");
  });
});
