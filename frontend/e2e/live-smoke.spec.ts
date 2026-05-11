import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.on('console', (message) => {
    if (['warning', 'error'].includes(message.type())) {
      throw new Error(`Console ${message.type()}: ${message.text()}`);
    }
  });
  page.on('pageerror', (error) => {
    throw error;
  });
});

test('live dashboard renders seeded inbox through real HTTP', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByText('Naruon Mail')).toBeVisible();
  await expect(page.getByText('Live E2E Release')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText('Failed to load emails.')).toHaveCount(0);
});
