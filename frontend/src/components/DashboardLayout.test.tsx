/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

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
    const mailNav = container.querySelector('nav[aria-label="Mail sections"]');
    const aiNav = container.querySelector('nav[aria-label="AI workspace sections"]');
    const mobileNav = container.querySelector('nav[aria-label="Mobile workspace sections"]');
    const mobileMenuButton = container.querySelector<HTMLButtonElement>('button[aria-label="Open workspace menu"]');
    const mobileNavButtons = Array.from(mobileNav?.querySelectorAll('button') ?? []).map(
      (button) => button.textContent,
    );
    const main = container.querySelector("main#main-content");
    const skipLink = container.querySelector<HTMLAnchorElement>(
      'a[href="#main-content"]',
    );
    const logo = container.querySelector<HTMLImageElement>('img[alt="Naruon"]');

    expect(banner).not.toBeNull();
    expect(sidebar).not.toBeNull();
    expect(nav).not.toBeNull();
    expect(mailNav).not.toBeNull();
    expect(aiNav).not.toBeNull();
    expect(mobileNav).not.toBeNull();
    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("false");
    expect(mobileMenuButton?.getAttribute("aria-controls")).toBe("mobile-workspace-menu");
    expect(mobileNavButtons).toEqual(["받은편지함", "맥락 검색", "AI 실행", "일정"]);
    expect(main).not.toBeNull();
    expect(skipLink).not.toBeNull();
    expect(logo?.getAttribute("src")).toBe("/brand/naruon-logo.svg");
    expect(sidebar?.textContent ?? "").toContain("Naruon");
    expect(sidebar?.textContent ?? "").toContain("흐름을 건너, 더 나은 판단과 실행으로.");
    expect(mailNav?.textContent ?? "").toContain("받은 메일");
    expect(mailNav?.textContent ?? "").toContain("중요 메일");
    expect(nav?.textContent ?? "").toContain("받은편지함");
    expect(nav?.textContent ?? "").toContain("맥락 종합");
    expect(nav?.textContent ?? "").toContain("판단 포인트");
    expect(nav?.textContent ?? "").toContain("실행 항목");
    expect(nav?.textContent ?? "").toContain("일정 연결");
    expect(aiNav?.textContent ?? "").toContain("판단 포인트");
    expect(banner?.textContent ?? "").toContain("캘린더 반영");
    expect(banner?.textContent ?? "").toContain("답장 초안");
    expect(banner?.textContent ?? "").toContain("할 일 만들기");
    expect(skipLink?.textContent).toBe("Skip to main content");
    expect(main?.textContent ?? "").toContain("Inbox workspace content");

    act(() => {
      mobileMenuButton?.click();
    });

    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("true");
    expect(container.querySelector('#mobile-workspace-menu')?.textContent ?? "").toContain("판단 포인트");
  });

  it("routes mobile workspace menu items to primary mobile views", () => {
    const handleMobileViewChange = vi.fn();
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(
        <DashboardLayout mobileView="inbox" onMobileViewChange={handleMobileViewChange}>
          <section>Inbox workspace content</section>
        </DashboardLayout>,
      );
    });

    const mobileMenuButton = container.querySelector<HTMLButtonElement>('button[aria-label="Open workspace menu"]');
    act(() => {
      mobileMenuButton?.click();
    });

    const executionLink = Array.from(
      container.querySelectorAll<HTMLAnchorElement>('#mobile-workspace-menu a'),
    ).find((link) => link.textContent?.includes("실행 항목"));

    act(() => {
      executionLink?.click();
    });

    expect(handleMobileViewChange).toHaveBeenCalledWith("actions");
    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("false");
  });
});
