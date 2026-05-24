import { test, expect } from '@playwright/test';

test.describe('Mobile Responsive & Hamburger Menu', () => {
  test.use({ viewport: { width: 375, height: 812 } }); // iPhone X viewport

  test('Hamburger menu toggles correctly and manages overlay', async ({ page }) => {
    await page.goto('/');

    // Ensure the hamburger button is visible
    const hamburgerBtn = page.getByRole('button', { name: '워크스페이스 메뉴 열기' });
    await expect(hamburgerBtn).toBeVisible();

    // The menu should be initially hidden
    const menu = page.locator('#mobile-workspace-menu');
    await expect(menu).not.toBeVisible();

    // Click to open
    await hamburgerBtn.click();
    await expect(menu).toBeVisible();
    await expect(hamburgerBtn).toHaveAttribute('aria-expanded', 'true');

    // Check if the backdrop is visible
    const backdrop = page.getByTestId('mobile-workspace-backdrop');
    await expect(backdrop).toBeVisible();

    // Close by clicking backdrop
    await backdrop.click();

    await expect(menu).not.toBeVisible();
    await expect(hamburgerBtn).toHaveAttribute('aria-expanded', 'false');
  });

  test('Hamburger menu closes when close button is clicked', async ({ page }) => {
    await page.goto('/');

    const hamburgerBtn = page.getByRole('button', { name: '워크스페이스 메뉴 열기' });
    await hamburgerBtn.click();
    
    const menu = page.locator('#mobile-workspace-menu');
    await expect(menu).toBeVisible();
    
    // Close by clicking the close button
    const closeBtn = page.getByRole('button', { name: '모바일 워크스페이스 메뉴 닫기' });
    await expect(closeBtn).toBeVisible();
    await closeBtn.click();

    await expect(menu).not.toBeVisible();
    await expect(hamburgerBtn).toHaveAttribute('aria-expanded', 'false');
  });

  test('Bottom action bars and panels have safe-area padding', async ({ page }) => {
    await page.goto('/');

    // Check bottom navigation has safe area padding class
    const bottomNav = page.locator('nav[aria-label="Mobile workspace sections"]');
    await expect(bottomNav).toBeVisible();
    
    const bottomVal = await bottomNav.evaluate((el) => window.getComputedStyle(el).bottom);
    expect(parseFloat(bottomVal) || 0).toBeGreaterThanOrEqual(12);
  });
});
