import { expect, test } from '@playwright/test';

import { mockDashboardApi } from './helpers';

test('renders the desktop Naruon shell with local brand assets', async ({ page }) => {
  const requestedUrls: string[] = [];
  page.on('request', (request) => requestedUrls.push(request.url()));
  await mockDashboardApi(page);

  await page.goto('/');

  await expect(page.getByRole('img', { name: 'Naruon' })).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Mail sections' })).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Naruon workspace sections' })).toBeVisible();
  await expect(page.getByText('흐름을 건너, 더 나은 판단과 실행으로.')).toBeVisible();
  const header = page.locator('header[aria-label="Naruon workspace header"]');
  await expect(header.getByText('캘린더 반영')).toBeVisible();
  await expect(header.getByText('답장 초안')).toBeVisible();
  await expect(header.getByText('할 일 만들기')).toBeVisible();
  await expect(header.getByRole('button', { name: '캘린더 반영' })).toHaveCount(0);
  await expect(header.getByRole('button', { name: '답장 초안' })).toHaveCount(0);
  await expect(header.getByRole('button', { name: '할 일 만들기' })).toHaveCount(0);
  await expect(page.getByText('Q2 출시 계획 및 우선순위 조정')).toBeVisible();

  expect(requestedUrls.some((url) => /fonts\.(googleapis|gstatic)\.com/.test(url))).toBe(false);
});

test('renders compact mobile navigation without hover-only controls', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockDashboardApi(page);

  await page.goto('/');

  await expect(page.getByRole('navigation', { name: 'Mobile workspace sections' })).toBeVisible();
  await expect(page.getByRole('button', { name: '받은편지함' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'AI 실행' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Open workspace menu' })).toBeVisible();
});
