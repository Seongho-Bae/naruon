import { test, expect } from '@playwright/test';

import { mockDashboardApi } from './helpers';

test.describe('Mobile Workspace Navigation', () => {
  test.use({ viewport: { width: 375, height: 812 } }); // iPhone X viewport

  test('hamburger menu toggles and displays correctly', async ({ page }, testInfo) => {
    await mockDashboardApi(page);
    await page.goto('/');

    // Wait for the main app to render
    const menuButton = page.locator('button[aria-label="워크스페이스 메뉴 열기"]');
    await expect(menuButton).toBeVisible();

    // Click to open the mobile menu
    await menuButton.click();

    const mobileMenu = page.locator('#mobile-workspace-menu');
    await expect(mobileMenu).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.body.style.overflow)).toBe('hidden');

    // Verify some expected elements in the menu
    await expect(mobileMenu.getByText('시작 화면', { exact: true })).toBeVisible();
    await expect(mobileMenu.getByText('워크스페이스 메뉴', { exact: true })).toBeVisible();
    await expect(mobileMenu.getByRole('link', { name: /데이터/ })).toBeVisible();
    await expect(mobileMenu.getByRole('link', { name: /보안/ })).toBeVisible();

    await page.screenshot({ path: testInfo.outputPath('mobile-hamburger-open.png'), fullPage: false });

    const drawerScrollMetrics = await mobileMenu.evaluate((drawer) => {
      const before = drawer.scrollTop;
      drawer.scrollTop = drawer.scrollHeight;
      return {
        before,
        after: drawer.scrollTop,
        maxScroll: drawer.scrollHeight - drawer.clientHeight,
      };
    });
    expect(drawerScrollMetrics.maxScroll).toBeGreaterThan(0);
    expect(drawerScrollMetrics.after).toBeGreaterThan(drawerScrollMetrics.before);

    await page.screenshot({ path: testInfo.outputPath('mobile-hamburger-open-scrolled.png'), fullPage: false });

    // Close the menu
    const closeButton = page.locator('button[aria-label="모바일 워크스페이스 메뉴 닫기"]');
    await closeButton.click();

    // Playwright popover might need a moment to hide
    await expect(mobileMenu).not.toBeVisible();
    await expect.poll(() => page.evaluate(() => document.body.style.overflow)).not.toBe('hidden');
  });
});
