/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

const apiClientMock = vi.hoisted(() => ({
  get: vi.fn(async () => ({ emails: [] })),
  canManageWorkspaceSettings: vi.fn(() => false),
}));

vi.mock("@/lib/api-client", () => ({
  apiClient: apiClientMock,
}));

import { DashboardLayout } from "./DashboardLayout";

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

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
    vi.clearAllMocks();
    apiClientMock.canManageWorkspaceSettings.mockReturnValue(false);
  });

  it("renders the Naruon branded shell with accessible navigation landmarks", async () => {
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
    await flushAsyncWork();

    const banner = container.querySelector('header[aria-label="Naruon workspace header"]');
    const sidebar = container.querySelector('aside[aria-label="Naruon workspace sidebar"]');
    const nav = container.querySelector('nav[aria-label="Mail sections"]');
    const desktopSidebarText = sidebar?.textContent ?? "";
    const workspaceNav = container.querySelector('nav[aria-label="워크스페이스 맥락 메뉴"]');
    const headerSearch = container.querySelector<HTMLFormElement>('form[aria-label="Header context search"]');
    const headerSearchInput = headerSearch?.querySelector<HTMLInputElement>('input[name="q"]');
    const mainScrollSection = container.querySelector<HTMLElement>('main#main-content > section');
    const mobileDrawer = container.querySelector<HTMLElement>('#mobile-workspace-menu');
    const mobileNav = container.querySelector('nav[aria-label="Mobile workspace sections"]');
    const mobileMenuButton = container.querySelector<HTMLButtonElement>('button[aria-label="Open workspace menu"]');
    const mobileNavButtons = Array.from(mobileNav?.querySelectorAll('a') ?? []).map(
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
    expect(workspaceNav).not.toBeNull();
    expect(desktopSidebarText).toContain("설정");
    expect(desktopSidebarText).not.toContain("Prompt Studio");
    expect(container.querySelector('aside a[href="/settings"] svg')).not.toBeNull();
    expect(container.querySelector('aside a[href="/prompt-studio"]')).toBeNull();
    expect(headerSearch).not.toBeNull();
    expect(headerSearch?.getAttribute("action")).toBe("/ai-hub/context");
    expect(headerSearch?.getAttribute("method")?.toLowerCase()).toBe("get");
    expect(headerSearchInput?.getAttribute("type")).toBe("search");
    expect(headerSearchInput?.getAttribute("name")).toBe("q");
    expect(mainScrollSection?.className).toContain("pb-[calc(5.5rem+env(safe-area-inset-bottom))]");
    expect(mobileDrawer?.textContent ?? "").toContain("메일 작성");
    expect(mobileDrawer?.textContent ?? "").toContain("중요 메일");
    expect(mobileDrawer?.textContent ?? "").toContain("보낸 메일");
    expect(mobileDrawer?.textContent ?? "").toContain("임시 보관함");
    expect(mobileDrawer?.textContent ?? "").toContain("전체 메일");
    expect(mobileDrawer?.textContent ?? "").toContain("프로젝트");
    expect(mobileDrawer?.textContent ?? "").toContain("라벨");
    expect(mobileDrawer?.textContent ?? "").toContain("설정");
    expect(mobileNav).not.toBeNull();
    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("false");
    expect(mobileMenuButton?.getAttribute("aria-controls")).toBe("mobile-workspace-menu");
    expect(mobileNavButtons).toEqual(["받은 메일", "맥락 종합", "판단 포인트", "실행 항목", "설정"]);
    expect(mobileNav?.className).toContain("pb-[calc(0.5rem+env(safe-area-inset-bottom))]");
    expect(mobileNav?.className).toContain("bottom-[calc(0.75rem+env(safe-area-inset-bottom))]");
    expect(Array.from(container.querySelectorAll('nav[aria-label="워크스페이스 작업면"] a')).map((link) => link.getAttribute('href'))).toEqual([
      '/',
      '/ai-hub/context',
      '/ai-hub/decisions',
      '/ai-hub/actions',
      '#main-content',
    ]);
    expect(main).not.toBeNull();
    expect(skipLink).not.toBeNull();
    expect(logo?.getAttribute("src")).toBe("/brand/naruon-logo.svg");
    expect(sidebar?.textContent ?? "").not.toContain("흐름을 건너, 더 나은 판단과 실행으로.");
    expect(sidebar?.textContent ?? "").toContain("빠른 이동");
    expect(nav?.textContent ?? "").toContain("받은 메일");
    expect(banner?.textContent ?? "").toContain("오늘 검토");
    expect(banner?.textContent ?? "").not.toContain("맥락 종합");
    expect(skipLink?.textContent).toBe("Skip to main content");
    expect(main?.textContent ?? "").toContain("Inbox workspace content");

    act(() => {
      mobileMenuButton?.click();
    });
    await flushAsyncWork();

    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("true");
    expect(mobileDrawer?.hidden).toBe(false);
    expect(mobileDrawer?.getAttribute("role")).toBe("dialog");
    expect(mobileDrawer?.getAttribute("aria-modal")).toBe("true");
    expect(mobileDrawer?.getAttribute("aria-labelledby")).toBe("mobile-workspace-menu-title");
    expect(container.querySelector('[data-testid="mobile-workspace-backdrop"]')).not.toBeNull();
  });

  it("closes the mobile drawer with keyboard and backdrop actions while returning focus", async () => {
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
    await flushAsyncWork();

    const mobileMenuButton = container.querySelector<HTMLButtonElement>('button[aria-label="Open workspace menu"]');
    mobileMenuButton?.focus();

    act(() => {
      mobileMenuButton?.click();
    });
    await flushAsyncWork();

    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("true");
    expect(document.activeElement?.textContent).toContain("메일 작성");

    act(() => {
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    });
    await flushAsyncWork();

    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("false");
    expect(document.activeElement).toBe(mobileMenuButton);

    act(() => {
      mobileMenuButton?.click();
    });
    await flushAsyncWork();

    const backdrop = container.querySelector<HTMLElement>('[data-testid="mobile-workspace-backdrop"]');
    act(() => {
      backdrop?.click();
    });
    await flushAsyncWork();

    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("false");
    expect(document.activeElement).toBe(mobileMenuButton);
  });

  it("layers the mobile drawer backdrop above the bottom navigation while keeping the drawer on top", async () => {
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
    await flushAsyncWork();

    const mobileMenuButton = container.querySelector<HTMLButtonElement>('button[aria-label="Open workspace menu"]');
    act(() => {
      mobileMenuButton?.click();
    });
    await flushAsyncWork();

    const backdrop = container.querySelector<HTMLElement>('[data-testid="mobile-workspace-backdrop"]');
    const drawer = container.querySelector<HTMLElement>('#mobile-workspace-menu');
    const bottomNav = container.querySelector<HTMLElement>('nav[aria-label="Mobile workspace sections"]');

    expect(backdrop?.className).toContain("z-50");
    expect(drawer?.className).toContain("z-[60]");
    expect(bottomNav?.className).toContain("z-40");
  });

  it("does not restore focus to the mobile menu opener after drawer link activation", async () => {
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
    await flushAsyncWork();

    const mobileMenuButton = container.querySelector<HTMLButtonElement>('button[aria-label="Open workspace menu"]');
    act(() => {
      mobileMenuButton?.focus();
      mobileMenuButton?.click();
    });
    await flushAsyncWork();

    const composeLink = Array.from(container.querySelectorAll<HTMLAnchorElement>('#mobile-workspace-menu a')).find(
      (link) => link.textContent?.includes("메일 작성"),
    );
    composeLink?.addEventListener("click", (event) => event.preventDefault(), { once: true });
    act(() => {
      composeLink?.focus();
      composeLink?.click();
    });
    await flushAsyncWork();

    expect(mobileMenuButton?.getAttribute("aria-expanded")).toBe("false");
    expect(document.activeElement).not.toBe(mobileMenuButton);
  });

  it("shows Prompt Studio navigation only for workspace admins", async () => {
    apiClientMock.canManageWorkspaceSettings.mockReturnValue(true);
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
    await flushAsyncWork();

    expect(container.textContent ?? "").toContain("Prompt Studio");
    expect(container.querySelector('aside a[href="/prompt-studio"]')).not.toBeNull();
  });

  it("keeps the desktop sidebar content reachable through an independent scroll region", async () => {
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
    await flushAsyncWork();

    const sidebar = container.querySelector<HTMLElement>('aside[aria-label="Naruon workspace sidebar"]');
    const scrollRegion = container.querySelector<HTMLElement>('[data-testid="sidebar-scroll-region"]');
    const contentSection = container.querySelector<HTMLElement>('main#main-content > section');
    const bottomNav = container.querySelector<HTMLElement>('nav[aria-label="Mobile workspace sections"]');
    const insightHeading = Array.from(container.querySelectorAll("p")).find(
      (element) => element.textContent === "오늘의 인사이트",
    );

    expect(sidebar?.className).toContain("overflow-hidden");
    expect(scrollRegion).not.toBeNull();
    expect(scrollRegion?.className).toContain("min-h-0");
    expect(scrollRegion?.className).toContain("overflow-y-auto");
    expect(contentSection?.className).toContain("overflow-y-auto");
    expect(bottomNav?.className).toContain("grid-cols-5");
    expect(bottomNav?.className).toContain("pb-[calc(0.5rem+env(safe-area-inset-bottom))]");
    expect(scrollRegion?.textContent ?? "").toContain("오늘의 인사이트");
    expect(insightHeading?.closest('[data-testid="sidebar-scroll-region"]')).toBe(scrollRegion);
  });

  it("restores sidebar scroll position across navigation renders", async () => {
    sessionStorage.setItem("naruon.sidebarScrollTop", "132");
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
    await flushAsyncWork();

    const scrollRegion = container.querySelector<HTMLElement>('[data-testid="sidebar-scroll-region"]');

    expect(scrollRegion?.scrollTop).toBe(132);
  });

});
