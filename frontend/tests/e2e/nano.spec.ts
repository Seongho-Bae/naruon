import { expect, test } from '@playwright/test';

test('nano test: verify user requested features', async ({ page }) => {
  // 1. Check AI Model Settings
  await page.goto('http://localhost:3000/settings');
  await expect(page.locator('text=Naruon').first()).toBeVisible();
  
  // Click AI Models tab (use visible=true to avoid strict mode violation and hidden elements on responsive layouts)
  await page.locator('button:has-text("AI 모델") >> visible=true').click();
  
  // Verify Model registration UI
  await expect(page.locator('text=로컬 모델 등록').first()).toBeVisible();
  await expect(page.locator('text=임베딩 모델 지정').first()).toBeVisible();
  
  // 2. Check Data page for email import
  await page.goto('http://localhost:3000/data');
  await expect(page.locator('text=이메일 반입').first()).toBeVisible();
});
