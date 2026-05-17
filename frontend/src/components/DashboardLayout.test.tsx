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
    localStorage.clear();
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
    const primaryNav = container.querySelector('nav[aria-label="Primary workspace navigation"]');
    const mobileNav = container.querySelector('nav[aria-label="Mobile workspace sections"]');
    const mobileQuickActionButton = container.querySelector<HTMLButtonElement>('button[aria-label="AI 빠른 실행"]');
    const mobileMenuButton = container.querySelector<HTMLButtonElement>('button[aria-label="Open workspace menu"]');
    const mobileNavLinks = Array.from(mobileNav?.querySelectorAll('a') ?? []).map(
      (link) => link.textContent,
    );
    const headerActionButtons = Array.from(
      banner?.querySelectorAll<HTMLButtonElement>('button[data-header-action]') ?? [],
    ).map((button) => button.textContent);
    const headerActionGroup = banner?.querySelector<HTMLElement>('[data-testid="header-action-group"]');
    const main = container.querySelector("main#main-content");
    const skipLink = container.querySelector<HTMLAnchorElement>(
      'a[href="#main-content"]',
    );
    const logo = container.querySelector<HTMLImageElement>('img[alt="Naruon"]');
    const comingSoonControls = Array.from(
      container.querySelectorAll<HTMLButtonElement>('button[data-coming-soon="true"]'),
    ).map((button) => button.textContent);
    const aiHubSectionNav = container.querySelector('nav[aria-label="Naruon workspace sections"]');

    expect(banner).not.toBeNull();
    expect(sidebar).not.toBeNull();
    expect(nav).not.toBeNull();
    expect(primaryNav?.textContent).toContain("홈");
    expect(primaryNav?.querySelector<HTMLAnchorElement>('a[href="/ai-hub"]')?.textContent).toContain("AI 허브");
    expect(primaryNav?.querySelector<HTMLAnchorElement>('a[href="/prompt-studio"]')?.textContent).toContain("프롬프트");
    expect(primaryNav?.querySelector<HTMLAnchorElement>('a[href="/settings"]')?.textContent).toContain("설정");
    expect(mobileNav).not.toBeNull();
    expect(banner?.querySelector('button[aria-label="알림 보기"]')).not.toBeNull();
    expect(banner?.querySelector('button[aria-label="프로필 메뉴"]')).not.toBeNull();
    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("false");
    expect(mobileMenuButton?.getAttribute("aria-controls")).toBe("mobile-workspace-menu");
    expect(mobileNavLinks).toEqual(["받은편지함", "맥락 검색", "일정", "더보기"]);
    expect(mobileQuickActionButton).not.toBeNull();
    expect(mobileQuickActionButton?.getAttribute("popovertarget")).toBe("mobile-ai-action-menu");
    expect(mobileQuickActionButton?.getAttribute("aria-haspopup")).toBe("dialog");
    expect(comingSoonControls.some((text) => text?.includes("중요 메일") && text.includes("준비 중"))).toBe(true);
    expect(comingSoonControls.some((text) => text?.includes("맥락 종합") && text.includes("준비 중"))).toBe(false);
    expect(comingSoonControls.some((text) => text?.includes("런칭 프로젝트") && text.includes("준비 중"))).toBe(false);
    expect(nav?.querySelector<HTMLAnchorElement>('a[href="/starred"]')).toBeNull();
    expect(sidebar?.querySelector<HTMLAnchorElement>('a[href="/projects#launch"]')?.textContent).toContain("런칭 프로젝트");
    expect(sidebar?.querySelector<HTMLAnchorElement>('a[href="/projects#vendor"]')?.textContent).toContain("벤더 관리");
    expect(sidebar?.querySelector<HTMLAnchorElement>('a[href="/projects#marketing"]')?.textContent).toContain("마케팅 캠페인");
    expect(aiHubSectionNav?.querySelector<HTMLAnchorElement>('a[href="/ai-hub#context"]')?.textContent).toContain("맥락 종합");
    expect(aiHubSectionNav?.querySelector<HTMLAnchorElement>('a[href="/ai-hub#decisions"]')?.textContent).toContain("판단 포인트");
    expect(aiHubSectionNav?.querySelector<HTMLAnchorElement>('a[href="/ai-hub#actions"]')?.textContent).toContain("실행 항목");
    expect(main).not.toBeNull();
    expect(skipLink).not.toBeNull();
    expect(logo?.getAttribute("src")).toBe("/brand/naruon-logo.svg");
    expect(sidebar?.textContent ?? "").toContain("Naruon");
    expect(sidebar?.textContent ?? "").toContain("흐름을 건너, 더 나은 판단과 실행으로.");
    expect(nav?.textContent ?? "").toContain("받은 메일");
    expect(headerActionButtons).toEqual(["캘린더 반영", "답장 초안", "할 일 만들기"]);
    expect(headerActionGroup?.className).toContain("lg:flex");
    expect(headerActionGroup?.className).not.toContain("xl:flex");
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
    const mobileMenu = container.querySelector<HTMLElement>('#mobile-workspace-menu');
    expect(mobileMenu?.textContent ?? "").toContain("시작 화면");
    expect(mobileMenu?.textContent ?? "").toContain("대시보드");
    expect(mobileMenu?.textContent ?? "").toContain("이메일");
    expect(mobileMenu?.textContent ?? "").toContain("일정");
    expect(mobileMenu?.textContent ?? "").toContain("메일");
    expect(mobileMenu?.textContent ?? "").toContain("워크스페이스");
    expect(mobileMenu?.textContent ?? "").toContain("도움");
    expect(mobileMenu?.querySelector<HTMLAnchorElement>('a[href="/settings"]')?.textContent).toContain("설정");
    expect(mobileMenu?.querySelector<HTMLAnchorElement>('a[href="#mobile-calendar"]')?.textContent).toContain("일정");
    expect(mobileMenu?.querySelector<HTMLButtonElement>('button[data-startup-view="calendar"]')).not.toBeNull();

    act(() => {
      mobileMenu?.querySelector<HTMLButtonElement>('button[data-startup-view="calendar"]')?.click();
    });

    expect(localStorage.getItem("naruon_startup_view")).toBe("calendar");
    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("false");

    const events: string[] = [];
    window.addEventListener("naruon:mobile-workspace", ((event: Event) => {
      events.push((event as CustomEvent<{ view: string }>).detail.view);
    }) as EventListener);

    act(() => {
      mobileQuickActionButton?.click();
    });

    expect(container.querySelector('#mobile-ai-action-menu')?.textContent ?? "").toContain("답장 초안");

    act(() => {
      container?.querySelector<HTMLButtonElement>('button[data-mobile-quick-action="create-task"]')?.click();
    });

    expect(headerEvents).toContain("create-task");

    const actionsNavLink = mobileNav?.querySelector<HTMLAnchorElement>('[data-mobile-view="actions"]');
    const actionsClick = new MouseEvent("click", { bubbles: true, cancelable: true });
    act(() => {
      actionsNavLink?.dispatchEvent(actionsClick);
    });

    expect(actionsClick.defaultPrevented).toBe(true);
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

  it("clears stale mobile hashes when switching startup back to dashboard", () => {
    window.history.replaceState(null, "", "/#mobile-calendar");
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

    const mobileMenuButton = container.querySelector<HTMLButtonElement>('button[aria-label="Open workspace menu"]');
    act(() => {
      mobileMenuButton?.click();
    });
    const mobileMenu = container.querySelector<HTMLElement>('#mobile-workspace-menu');

    act(() => {
      mobileMenu?.querySelector<HTMLButtonElement>('button[data-startup-view="dashboard"]')?.click();
    });

    expect(localStorage.getItem("naruon_startup_view")).toBe("dashboard");
    expect(window.location.hash).toBe("");
  });

});
