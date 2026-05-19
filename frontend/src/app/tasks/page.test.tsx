/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("lucide-react", () => ({
  CheckCircle2: () => <svg aria-hidden="true" />,
  Inbox: () => <svg aria-hidden="true" />,
  ListChecks: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  UserRoundCheck: () => <svg aria-hidden="true" />,
}));

import TasksPage from "./page";

describe("TasksPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
  });

  it("renders ticket tracking screens with source-linked task details", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<TasksPage />);
    });

    expect(container.querySelector("h1")?.textContent).toContain("할 일 추적");
    expect(container.textContent).toContain("내 작업");
    expect(container.textContent).toContain("위임한 작업");
    expect(container.textContent).toContain("칸반");
    expect(container.textContent).toContain("작업 상세");
    expect(container.textContent).toContain("접수");
    expect(container.textContent).toContain("진행");
    expect(container.textContent).toContain("차단");
    expect(container.textContent).toContain("완료");
    expect(container.textContent).toContain("원본 메일");
    expect(container.textContent).toContain("답변 추적");
    expect(container.textContent).not.toContain("Ticket tasks");
    expect(container.textContent).not.toContain("다음 구현 단계");
  });
});
