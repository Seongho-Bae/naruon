/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("lucide-react", () => ({
  Search: () => <svg aria-hidden="true" />,
  Mail: () => <svg aria-hidden="true" />,
  CalendarDays: () => <svg aria-hidden="true" />,
  FileText: () => <svg aria-hidden="true" />,
  UserRound: () => <svg aria-hidden="true" />,
  Network: () => <svg aria-hidden="true" />,
  Filter: () => <svg aria-hidden="true" />,
  Clock: () => <svg aria-hidden="true" />,
  ChevronRight: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
}));

import SearchPage from "./page";

describe("SearchPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
  });

  it("renders integrated search results detail graph and timeline states", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<SearchPage />);
    });

    expect(container.textContent).toContain("Q2 런칭 캠페인 기획안.pdf");
    expect(container.textContent).toContain("통합 검색");
  });
});
