/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it } from "vitest";

import { DashboardLayout } from "./DashboardLayout";

describe("DashboardLayout", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
  });

  it("renders the Naruon branded shell with accessible navigation landmarks", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(
        <DashboardLayout>
          <section>Inbox workspace content</section>
        </DashboardLayout>,
      );
    });

    const banner = container.querySelector('header[aria-label="Naruon workspace header"]');
    const sidebar = container.querySelector('aside[aria-label="Naruon workspace sidebar"]');
    const nav = container.querySelector('nav[aria-label="Naruon workspace sections"]');
    const main = container.querySelector("main#main-content");
    const skipLink = container.querySelector<HTMLAnchorElement>(
      'a[href="#main-content"]',
    );
    const decorativeMarks = container.querySelectorAll('svg[aria-hidden="true"]');
    const gradientIds = Array.from(container.querySelectorAll("linearGradient[id]"))
      .map((gradient) => gradient.id);

    expect(banner).not.toBeNull();
    expect(sidebar).not.toBeNull();
    expect(nav).not.toBeNull();
    expect(main).not.toBeNull();
    expect(skipLink).not.toBeNull();
    expect(sidebar?.textContent ?? "").toContain("Naruon");
    expect(sidebar?.textContent ?? "").toContain("흐름을 건너, 더 나은 판단과 실행으로.");
    expect(nav?.textContent ?? "").toContain("받은편지함");
    expect(nav?.textContent ?? "").toContain("맥락 종합");
    expect(nav?.textContent ?? "").toContain("판단 포인트");
    expect(nav?.textContent ?? "").toContain("실행 항목");
    expect(nav?.textContent ?? "").toContain("일정 연결");
    expect(skipLink?.textContent).toBe("Skip to main content");
    expect(main?.textContent ?? "").toContain("Inbox workspace content");
    expect(Array.from(decorativeMarks).every((mark) => !mark.hasAttribute("role"))).toBe(true);
    expect(new Set(gradientIds).size).toBe(gradientIds.length);
  });
});
