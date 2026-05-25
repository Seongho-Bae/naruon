import { test, expect } from '@playwright/test';

test.describe('Mobile Workspace Navigation', () => {
  test.use({ viewport: { width: 375, height: 812 } }); // iPhone X viewport

  test('hamburger menu toggles and displays correctly', async ({ page }) => {
    await page.goto('/');

    // Wait for the main app to render
    const menuButton = page.locator('button[aria-label="워크스페이스 메뉴 열기"]');
    await expect(menuButton).toBeVisible();

    // Click to open the mobile menu
    await menuButton.click();

    const mobileMenu = page.locator('#mobile-workspace-menu');
    await expect(mobileMenu).toBeVisible();

    // Verify some expected elements in the menu
    await expect(page.locator('text=시작 화면')).toBeVisible();
    await expect(page.locator('text=워크스페이스 메뉴')).toBeVisible();

    // Take a screenshot of the opened menu
    await page.screenshot({ path: 'test-results/mobile-hamburger-open.png', fullPage: false });

    // Close the menu
    const closeButton = page.locator('button[aria-label="모바일 워크스페이스 메뉴 닫기"]');
    await closeButton.click();

    // Playwright popover might need a moment to hide
    await expect(mobileMenu).not.toBeVisible();
  });
});
