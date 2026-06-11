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

test('nano test: verify user requested features', async ({ page }) => {
  const sessionToken = 'signed-nano-session';
  const providerRequestHeaders: Record<string, string>[] = [];
  await mockDashboardApi(page, (path, request) => {
    if (path === '/api/llm-providers' && request.method() === 'GET') {
      providerRequestHeaders.push(request.headers());
    }
  });
  await page.addInitScript((token) => {
    window.localStorage.setItem('naruon_session_token', token);
  }, sessionToken);

  // 1. Check AI Model Settings
  await page.goto('/settings');
  await expect(page.getByText('Naruon', { exact: false }).first()).toBeVisible();

  // Click AI Models tab (use visible=true to avoid strict mode violation and hidden elements on responsive layouts)
  await page.getByRole('button', { name: 'AI 모델' }).first().click();

  await expect.poll(() => providerRequestHeaders.length).toBeGreaterThan(0);
  const headers = providerRequestHeaders.at(-1) ?? {};
  expect(headers.authorization).toBe(`Bearer ${sessionToken}`);
  for (const headerName of publicIdentityHeaders) {
    expect(headers[headerName]).toBeUndefined();
  }

  // Verify Model registration UI
  await expect(page.getByText('로컬 모델 등록', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('임베딩 모델 지정', { exact: true }).first()).toBeVisible();

  // 2. Check Data page for email import
  await page.goto('/data');
  await expect(page.getByText('이메일 반입', { exact: false }).first()).toBeVisible();
});
