import { expect, test, type Browser, type BrowserContextOptions, type Page } from '@playwright/test';

import { mockDashboardApi } from './helpers';

const APP_URL = process.env.LIVE_BASE_URL ?? 'http://127.0.0.1:3001';

async function createMockedPage(browser: Browser, options?: BrowserContextOptions): Promise<Page> {
  const context = await browser.newContext(options);
  const page = await context.newPage();
  await mockDashboardApi(page);
  return page;
}

test('renders the desktop Naruon shell with local brand assets', async ({ browser }) => {
  const page = await createMockedPage(browser, { viewport: { width: 1440, height: 960 } });
  const requestedUrls: string[] = [];
  page.on('request', (request) => requestedUrls.push(request.url()));

  await page.goto(`${APP_URL}/`);

  await expect(page.locator('img[alt="Naruon"]')).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Mail sections' })).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'AI Hub sections' })).toBeVisible();
  await expect(page.getByText('빠른 이동')).toBeVisible();
  const header = page.locator('header[aria-label="Naruon workspace header"]');
  await expect(header.getByText('오늘 검토')).toBeVisible();
  await expect(header.getByText('실행 대기')).toBeVisible();
  await expect(page.getByText('오늘의 판단 포인트')).toBeVisible();
  await expect(page.getByText('빠른 실행')).toBeVisible();
  await expect(page.getByRole('link', { name: '판단 포인트' }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: '판단 포인트' })).toBeVisible();
  await expect(page.getByText('메일을 불러오는 중입니다...')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Q2 출시 계획 및 우선순위 조정 메일. 오른쪽으로 밀면 실행 목록에 담고, 왼쪽으로 밀면 완료 처리합니다.' })).toBeVisible();

  expect(
    requestedUrls.some((url) => {
      const hostname = new URL(url).hostname;
      return hostname === 'fonts.googleapis.com' || hostname === 'fonts.gstatic.com';
    }),
  ).toBe(false);

  await page.context().close();
});

test('keeps sidebar scroll position when navigating after scrolling the menu', async ({ browser }) => {
  const page = await createMockedPage(browser, { viewport: { width: 1440, height: 960 } });

  await page.goto(`${APP_URL}/`);
  await page.locator('[data-testid="sidebar-scroll-region"]').evaluate((element) => {
    element.scrollTop = 240;
    sessionStorage.setItem('naruon.sidebarScrollTop', '240');
  });

  await page.goto(`${APP_URL}/settings`);

  await expect(page.locator('main#main-content > section')).toHaveJSProperty('scrollTop', 0);
  await expect.poll(async () => page.locator('[data-testid="sidebar-scroll-region"]').evaluate((element) => element.scrollTop)).toBe(240);

  await page.context().close();
});

test('keeps mobile navigation on one row and content scrollable across target devices', async ({ browser }) => {
  const profiles = [
    { name: 'iphone-se', viewport: { width: 375, height: 667 }, deviceScaleFactor: 2 },
    { name: 'iphone-14-pro-max', viewport: { width: 430, height: 932 }, deviceScaleFactor: 3 },
    { name: 'android-small', viewport: { width: 360, height: 800 }, deviceScaleFactor: 2.75 },
    { name: 'ipad-mini', viewport: { width: 768, height: 1024 }, deviceScaleFactor: 2 },
  ];

  for (const profile of profiles) {
    const context = await browser.newContext({
      viewport: profile.viewport,
      deviceScaleFactor: profile.deviceScaleFactor,
      hasTouch: true,
      isMobile: profile.viewport.width < 820,
    });
    const mobilePage = await context.newPage();
    await mockDashboardApi(mobilePage);

    await mobilePage.goto(`${APP_URL}/ai-hub/actions`);
    await expect(mobilePage.getByRole('navigation', { name: 'Mobile workspace sections' })).toBeVisible();
    await expect(mobilePage.getByRole('heading', { name: '실행 항목' })).toBeVisible();

    const metrics = await mobilePage.locator('body').evaluate(() => {
      const section = document.querySelector('main#main-content > section');
      const bottomNav = document.querySelector('nav[aria-label="Mobile workspace sections"]');
      section?.scrollTo({ top: section.scrollHeight, behavior: 'instant' });
      const interactiveItems = section
        ? Array.from(section.querySelectorAll('a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'))
        : [];
      const lastInteractive = interactiveItems.at(-1);
      const items = [...document.querySelectorAll('nav[aria-label="Mobile workspace sections"] a')].map((el) => ({
        text: el.textContent?.trim(),
        top: Math.round(el.getBoundingClientRect().top),
      }));
      const navBox = bottomNav?.getBoundingClientRect();
      const lastBox = lastInteractive?.getBoundingClientRect();
      return {
        itemCount: items.length,
        uniqueTops: [...new Set(items.map((item) => item.top))],
        overflowY: section ? getComputedStyle(section).overflowY : null,
        bottomNavClassName: bottomNav ? bottomNav.className : null,
        lastInteractiveBottom: lastBox ? Math.round(lastBox.bottom) : null,
        bottomNavTop: navBox ? Math.round(navBox.top) : null,
      };
    });

    expect(metrics.itemCount, profile.name).toBe(5);
    expect(metrics.uniqueTops, profile.name).toHaveLength(1);
    expect(metrics.overflowY, profile.name).toBe('auto');
    expect(metrics.bottomNavClassName, profile.name).toContain('pb-[calc(0.5rem+env(safe-area-inset-bottom))]');
    if (metrics.lastInteractiveBottom !== null && metrics.bottomNavTop !== null) {
      expect(metrics.lastInteractiveBottom, profile.name).toBeLessThanOrEqual(metrics.bottomNavTop - 4);
    }

    await context.close();
  }
});
