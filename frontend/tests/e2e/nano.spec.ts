import { expect, test } from '@playwright/test';

test('nano test: verify user requested features', async ({ page }) => {
  // 1. Check AI Model Settings
  await page.goto('/settings');
  await expect(page.getByText('Naruon', { exact: false }).first()).toBeVisible();

  // Click AI Models tab (use visible=true to avoid strict mode violation and hidden elements on responsive layouts)
  await page.getByRole('button', { name: 'AI 모델' }).first().click();

  // Verify Model registration UI
  await expect(page.getByText('로컬 모델 등록', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('임베딩 모델 지정', { exact: true }).first()).toBeVisible();

  // 2. Check Data page for email import
  await page.goto('/data');
  await expect(page.getByText('이메일 반입', { exact: false }).first()).toBeVisible();
});
