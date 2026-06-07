import { test, expect } from '@playwright/test';

import { mockDashboardApi } from './helpers';

test.describe('Scrolling behavior', () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test('main content should be scrollable on mobile', async ({ page }) => {
    await mockDashboardApi(page);
    await page.goto('/');

    // Wait for the main app to render
    const mainContent = page.locator('#main-content');
    await expect(mainContent).toBeVisible();

    // The DashboardLayout has <main id="main-content" className="flex min-w-0 flex-1 flex-col overflow-hidden pb-16 lg:pb-0">
    // and inside it <section className="min-h-0 flex-1 overflow-hidden p-3 lg:p-4"> 
    // Wait, the inner section might have overflow-y-auto instead of overflow-hidden if it is scrollable.
    // Let's check the bounding box or scroll position.
    
    // We expect to find the "안녕하세요" text and be able to scroll it if it has enough content.
    const heading = page.locator('h1', { hasText: '안녕하세요' });
    await expect(heading).toBeVisible();
    
    const scrollContainer = page.locator('[role="region"][aria-label="홈 개요 대시보드"]');
    const scrollState = await scrollContainer.evaluate((node) => {
      const element = node as HTMLElement;
      const previousTop = element.scrollTop;
      element.scrollTop = element.scrollHeight;
      return {
        clientHeight: element.clientHeight,
        previousTop,
        scrollHeight: element.scrollHeight,
        scrollTop: element.scrollTop,
      };
    });

    expect(scrollState.scrollHeight).toBeGreaterThan(scrollState.clientHeight);
    expect(scrollState.scrollTop).toBeGreaterThan(scrollState.previousTop);
  });
});
