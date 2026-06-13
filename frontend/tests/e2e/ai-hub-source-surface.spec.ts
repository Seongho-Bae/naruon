import { expect, test } from '@playwright/test';

import { mockDashboardApi } from './helpers';

const publicIdentityHeaders = [
  'x-user-id',
  'x-organization-id',
  'x-group-id',
  'x-group-ids',
  'x-user-role',
  'x-dev-auth-token',
];

const viewports = [
  { name: 'desktop', width: 1280, height: 720 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 390, height: 844 },
] as const;

for (const viewport of viewports) {
  test(`renders source-backed AI Hub with scroll at ${viewport.name}`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await mockDashboardApi(page);

    const surfaceRequest = page.waitForRequest((request) => {
      const url = new URL(request.url());
      return url.pathname === '/api/ai-hub/surface' && request.method() === 'GET';
    });

    await page.goto('/ai-hub');
    const headers = (await surfaceRequest).headers();
    expect(headers.authorization).toBeUndefined();
    for (const headerName of publicIdentityHeaders) {
      expect(headers[headerName]).toBeUndefined();
    }

    await expect(page.getByRole('heading', { name: 'AI 허브' })).toBeVisible();
    await expect(page.getByText('의사결정 로그 요약')).toBeVisible();
    await page.getByRole('button', { name: /워크플로우/ }).click();
    await expect(page.getByText('의사결정 로그 요약 실행 흐름')).toBeVisible();
    await page.getByRole('button', { name: /AI 에이전트/ }).click();
    await expect(page.getByText('Primary OpenAI')).toBeVisible();
    await page.getByRole('button', { name: /평가/ }).click();
    await expect(page.getByText('Provider 준비도')).toBeVisible();
    await page.getByRole('button', { name: /실행 이력/ }).click();
    await expect(page.getByText('api.llm_providers')).toBeVisible();

    const horizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(horizontalOverflow).toBeLessThanOrEqual(1);

    const aiHubScroller = page.locator('main').last();
    const scrollMetrics = await aiHubScroller.evaluate((node) => {
      const element = node as HTMLElement;
      element.scrollTop = 0;
      const before = element.scrollTop;
      element.scrollTop = element.scrollHeight;
      return {
        before,
        after: element.scrollTop,
        maxScroll: element.scrollHeight - element.clientHeight,
      };
    });
    expect(scrollMetrics.maxScroll).toBeGreaterThan(0);
    expect(scrollMetrics.after).toBeGreaterThan(scrollMetrics.before);

    await page.screenshot({ path: testInfo.outputPath(`ai-hub-${viewport.name}-scrolled.png`), fullPage: false });

    if (viewport.name === 'mobile') {
      await page.getByRole('button', { name: '워크스페이스 메뉴 열기' }).click();
      const mobileMenu = page.locator('#mobile-workspace-menu');
      await expect(mobileMenu).toBeVisible();
      await expect(mobileMenu.getByRole('link', { name: /AI 허브/ })).toBeVisible();
      await page.screenshot({ path: testInfo.outputPath('ai-hub-mobile-hamburger.png'), fullPage: false });
    }
  });
}
