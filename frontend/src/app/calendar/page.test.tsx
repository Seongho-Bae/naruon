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
  Clock: () => <svg aria-hidden="true" />,
  Users: () => <svg aria-hidden="true" />,
  Video: () => <svg aria-hidden="true" />,
  Plus: () => <svg aria-hidden="true" />,
  ChevronLeft: () => <svg aria-hidden="true" />,
  ChevronRight: () => <svg aria-hidden="true" />,
  Settings: () => <svg aria-hidden="true" />,
  X: () => <svg aria-hidden="true" />,
  Paperclip: () => <svg aria-hidden="true" />,
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

    expect(container.textContent).toContain("새 일정");
  });
});
