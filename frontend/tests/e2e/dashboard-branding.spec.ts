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
  await expect(page.getByRole('navigation', { name: 'Primary workspace navigation' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'AI 허브' })).toHaveAttribute('href', '/ai-hub');
  await expect(page.getByRole('link', { name: '프롬프트' })).toHaveAttribute('href', '/prompt-studio');
  await expect(header.getByRole('button', { name: '알림 보기' })).toBeVisible();
  await expect(header.getByRole('button', { name: '프로필 메뉴' })).toBeVisible();
  await expect(header.getByRole('button', { name: '캘린더 반영' })).toBeVisible();
  await expect(header.getByRole('button', { name: '답장 초안' })).toBeVisible();
  await expect(header.getByRole('button', { name: '할 일 만들기' })).toBeVisible();
  await header.getByRole('button', { name: '답장 초안' }).click();
  await expect(header.getByText('메일 상세 패널에서 답장 초안을 생성합니다.')).toBeVisible();
  const desktopWorkspace = page.getByRole('region', { name: '데스크톱 메일 작업공간' });
  await expect(desktopWorkspace.getByText('메일을 선택하세요')).toBeVisible();
  await expect(page).not.toHaveURL(/#mobile-detail$/);

  expect(
    requestedUrls.some((url) => {
      const hostname = new URL(url).hostname;
      return hostname === 'fonts.googleapis.com' || hostname === 'fonts.gstatic.com';
    }),
  ).toBe(false);
});

test('renders compact mobile navigation without hover-only controls', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockDashboardApi(page);

  await page.goto('/#mobile-detail');

  await expect(page.getByRole('region', { name: '모바일 받은편지함' })).toBeVisible();

  await expect(page.getByRole('navigation', { name: 'Mobile workspace sections' })).toBeVisible();
  await expect(page.getByRole('link', { name: '받은편지함' })).toBeVisible();
  await expect(page.getByRole('link', { name: '맥락 검색' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'AI 빠른 실행' })).toBeVisible();
  await expect(page.getByRole('link', { name: '일정' })).toBeVisible();
  await expect(page.getByRole('link', { name: '더보기' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Open workspace menu' })).toBeVisible();

  const mobileAiButton = page.getByRole('button', { name: 'AI 빠른 실행' });
  await mobileAiButton.click();
  await expect(page.getByRole('dialog', { name: 'AI 빠른 실행 메뉴' })).toBeVisible();
  await expect(page.getByRole('button', { name: '답장 초안' })).toBeVisible();
  await page.getByRole('link', { name: '더보기' }).click();
  await expect(page.getByRole('region', { name: '모바일 AI 실행' })).toBeVisible();
  await expect(page.getByText('관계 맥락')).toBeVisible();

  await page.getByRole('link', { name: '맥락 검색' }).click();
  await expect(page.getByRole('region', { name: '모바일 맥락 검색' })).toBeVisible();
  await expect(page.getByText('메일, 첨부, 일정, 사람을 한 번에 검색합니다.')).toBeVisible();

  await page.getByRole('link', { name: '일정' }).click();
  await expect(page.getByRole('region', { name: '모바일 일정 연결' })).toBeVisible();
  await expect(page.getByText('캘린더 반영 대기')).toBeVisible();
});
