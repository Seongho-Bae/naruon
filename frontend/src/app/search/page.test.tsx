/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("lucide-react", () => ({
  CalendarDays: () => <svg aria-hidden="true" />,
  FileText: () => <svg aria-hidden="true" />,
  Mail: () => <svg aria-hidden="true" />,
  Network: () => <svg aria-hidden="true" />,
  Search: () => <svg aria-hidden="true" />,
  UserRound: () => <svg aria-hidden="true" />,
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

    expect(container.querySelector("h1")?.textContent).toContain("맥락 검색");
    expect(container.textContent).toContain("통합 검색");
    expect(container.textContent).toContain("결과 상세");
    expect(container.textContent).toContain("관계 그래프");
    expect(container.textContent).toContain("타임라인");
    expect(container.textContent).toContain("발신자 DAG");
    expect(container.querySelector('[role="status"]')?.textContent).toContain("검색 결과 3건");
    expect(container.textContent).toContain("개인 메일에서 회사 일정 후보 발견");
  });
});
