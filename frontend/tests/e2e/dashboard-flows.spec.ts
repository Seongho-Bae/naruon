import { expect, test } from '@playwright/test';

import { mockDashboardApi } from './helpers';

test('connects inbox selection to summary, execution, reply, calendar, and graph states', async ({ page }) => {
  await mockDashboardApi(page);

  await page.goto('/');
  await page.getByRole('button', { name: /김지현 PM/ }).click();

  await expect(page.getByText('출시 일정, 마케팅 계획, 파트너 미팅')).toBeVisible();
  await expect(page.getByText('2개 실행 항목')).toBeVisible();
  await expect(page.getByText('2개 메시지').nth(1)).toBeVisible();
  await expect(page.getByText('1개 노드와 1개 관계')).toBeVisible();

  await page.getByRole('button', { name: '캘린더 반영' }).last().click();
  await expect(page.getByText('Synced 2 events!')).toBeVisible();

  await page.getByRole('button', { name: 'AI 답장 초안' }).last().click();
  await expect(page.getByLabel('Reply draft')).toHaveValue('검토 후 일정과 우선순위를 정리해 공유드리겠습니다.');

  await page.getByRole('button', { name: '답장 보내기' }).click();
  await expect(page.getByText('Reply simulated in development mode. No email was delivered.')).toBeVisible();
});

test('submits branded inbox search against the search API', async ({ page }) => {
  await mockDashboardApi(page);

  await page.goto('/');
  await page.getByLabel('Search emails').fill('출시');
  await page.getByRole('button', { name: '검색' }).click();

  await expect(page.getByText('Q2 출시 계획 및 우선순위 조정')).toBeVisible();
});
