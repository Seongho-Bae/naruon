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
    const nav = container.querySelector('nav[aria-label="Mail sections"]');
    const mobileNav = container.querySelector('nav[aria-label="Mobile workspace sections"]');
    const mobileMenuButton = container.querySelector<HTMLButtonElement>('button[aria-label="Open workspace menu"]');
    const mobileNavLinks = Array.from(mobileNav?.querySelectorAll('a') ?? []).map(
      (link) => link.textContent,
    );
    const headerActionButtons = Array.from(
      banner?.querySelectorAll<HTMLButtonElement>('button[data-header-action]') ?? [],
    ).map((button) => button.textContent);
    const main = container.querySelector("main#main-content");
    const skipLink = container.querySelector<HTMLAnchorElement>(
      'a[href="#main-content"]',
    );
    const logo = container.querySelector<HTMLImageElement>('img[alt="Naruon"]');

    expect(banner).not.toBeNull();
    expect(sidebar).not.toBeNull();
    expect(nav).not.toBeNull();
    expect(mobileNav).not.toBeNull();
    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("false");
    expect(mobileMenuButton?.getAttribute("aria-controls")).toBe("mobile-workspace-menu");
    expect(mobileNavLinks).toEqual(["받은편지함", "맥락 검색", "AI 실행", "일정"]);
    expect(main).not.toBeNull();
    expect(skipLink).not.toBeNull();
    expect(logo?.getAttribute("src")).toBe("/brand/naruon-logo.svg");
    expect(sidebar?.textContent ?? "").toContain("Naruon");
    expect(sidebar?.textContent ?? "").toContain("흐름을 건너, 더 나은 판단과 실행으로.");
    expect(nav?.textContent ?? "").toContain("받은 메일");
    expect(headerActionButtons).toEqual(["캘린더 반영", "답장 초안", "할 일 만들기"]);
    expect(skipLink?.textContent).toBe("Skip to main content");
    expect(main?.textContent ?? "").toContain("Inbox workspace content");

    const headerEvents: string[] = [];
    window.addEventListener("naruon:header-action", ((event: Event) => {
      headerEvents.push((event as CustomEvent<{ action: string }>).detail.action);
    }) as EventListener);

    act(() => {
      banner?.querySelector<HTMLButtonElement>('button[data-header-action="reply-draft"]')?.click();
    });

    expect(headerEvents).toContain("reply-draft");

    act(() => {
      mobileMenuButton?.click();
    });

    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("true");

    const events: string[] = [];
    window.addEventListener("naruon:mobile-workspace", ((event: Event) => {
      events.push((event as CustomEvent<{ view: string }>).detail.view);
    }) as EventListener);

    act(() => {
      mobileNav?.querySelector<HTMLElement>('[data-mobile-view="actions"]')?.click();
    });

    expect(events).toContain("actions");
  });

  it("keeps the desktop sidebar content reachable through an independent scroll region", () => {
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

    const sidebar = container.querySelector<HTMLElement>('aside[aria-label="Naruon workspace sidebar"]');
    const scrollRegion = container.querySelector<HTMLElement>('[data-testid="sidebar-scroll-region"]');
    const insightHeading = Array.from(container.querySelectorAll("p")).find(
      (element) => element.textContent === "오늘의 인사이트",
    );

    expect(sidebar?.className).toContain("overflow-hidden");
    expect(scrollRegion).not.toBeNull();
    expect(scrollRegion?.className).toContain("min-h-0");
    expect(scrollRegion?.className).toContain("overflow-y-auto");
    expect(scrollRegion?.textContent ?? "").toContain("오늘의 인사이트");
    expect(insightHeading?.closest('[data-testid="sidebar-scroll-region"]')).toBe(scrollRegion);
  });

});
