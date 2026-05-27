import { expect, test } from '@playwright/test';

import { mockDashboardApi } from './helpers';

test('renders the desktop Naruon shell with local brand assets', async ({ page }) => {
  const requestedUrls: string[] = [];
  page.on('request', (request) => requestedUrls.push(request.url()));
  await page.setViewportSize({ width: 1280, height: 1024 });
  await mockDashboardApi(page);

  await page.goto('/');

  await expect(page.getByRole('img', { name: 'Naruon' })).toBeVisible();
  // Sidebars and extra navigations were removed to match the unified top header branding.
  const header = page.locator('header[aria-label="Naruon workspace header"]');
  const primaryNav = page.getByRole('navigation', { name: 'Primary workspace navigation' });
  await expect(primaryNav).toBeVisible();
  await expect(primaryNav.getByRole('link', { name: '홈', exact: true })).toHaveAttribute('href', '/');
  await expect(primaryNav.getByRole('link', { name: '메일', exact: true })).toHaveAttribute('href', '/mail');
  await expect(primaryNav.getByRole('link', { name: '일정', exact: true })).toHaveAttribute('href', '/calendar');
  await expect(primaryNav.getByRole('link', { name: '작업', exact: true })).toHaveAttribute('href', '/tasks');
  await expect(primaryNav.getByRole('link', { name: '프로젝트', exact: true })).toHaveAttribute('href', '/projects');
  await expect(primaryNav.getByRole('link', { name: '맥락 검색', exact: true })).toHaveAttribute('href', '/search');
  await expect(primaryNav.getByRole('link', { name: 'AI 허브', exact: true })).toHaveAttribute('href', '/ai-hub');
  await expect(primaryNav.getByRole('link', { name: '데이터', exact: true })).toHaveAttribute('href', '/data');
  await expect(primaryNav.getByRole('link', { name: '보안', exact: true })).toHaveAttribute('href', '/security');
  await expect(primaryNav.getByRole('link', { name: '설정', exact: true })).toHaveAttribute('href', '/settings');
  await expect(header.getByRole('button', { name: '알림 보기' })).toBeVisible();
  await expect(header.getByRole('button', { name: '프로필 메뉴' })).toBeVisible();
  await expect(header.getByRole('button', { name: '캘린더 반영' })).toBeVisible();
  await expect(header.getByRole('button', { name: '답장 초안' })).toBeVisible();
  await expect(header.getByRole('button', { name: '할 일 만들기' })).toBeVisible();
  await header.getByRole('button', { name: '답장 초안' }).click();
  await expect(header.getByText('메일 상세 패널에서 답장 초안을 생성합니다.')).toBeVisible();
  await expect(header.getByText('메일 상세 패널에서 답장 초안을 생성합니다.')).toBeVisible();
  await expect(header.getByText('메일 상세 패널에서 답장 초안을 생성합니다.')).toBeVisible();

  await expect(page.getByRole('region', { name: '홈 개요 대시보드' }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: '메일함 바로가기' }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: '일정 확인하기' }).first()).toBeVisible();
  await page.getByRole('button', { name: '메일함 바로가기' }).first().click();
  const desktopWorkspace = page.getByRole('region', { name: '데스크톱 메일 작업공간' });
  await expect(desktopWorkspace.getByText('메일을 선택하세요')).toBeVisible();
  await expect(page).not.toHaveURL(/#mobile-detail$/);

  const desktopStartup = page.getByRole('region', { name: 'Desktop startup preference' });
  await expect(desktopStartup).toBeVisible();
  await expect(desktopStartup.getByRole('button', { name: '대시보드' })).toBeVisible();
  await expect(desktopStartup.getByRole('button', { name: '이메일' })).toBeVisible();
  await expect(desktopStartup.getByRole('button', { name: '일정' })).toBeVisible();

  expect(
    requestedUrls.some((url) => {
      const hostname = new URL(url).hostname;
      return hostname === 'fonts.googleapis.com' || hostname === 'fonts.gstatic.com';
    }),
  ).toBe(false);
  await expect(page.locator('link[rel="preload"][href="/brand/naruon-logo.svg"]')).toHaveCount(0);
});

test('keeps the short mobile AI quick action menu inside the viewport with scrollable actions', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 640 });
  await mockDashboardApi(page);

  await page.goto('/');
  await page.getByRole('button', { name: 'AI 빠른 실행' }).click();

  const menu = page.getByRole('dialog', { name: 'AI 빠른 실행 메뉴' });
  await expect(menu).toBeVisible();
  await expect(menu.getByRole('button', { name: '할 일 만들기' })).toBeVisible();
  const bounds = await menu.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    return { top: rect.top, bottom: rect.bottom, viewportHeight: window.innerHeight, overflowY: style.overflowY };
  });
  expect(bounds.top).toBeGreaterThanOrEqual(0);
  expect(bounds.bottom).toBeLessThanOrEqual(bounds.viewportHeight);
  expect(['auto', 'scroll']).toContain(bounds.overflowY);
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
  await expect(page.getByRole('button', { name: '워크스페이스 메뉴 열기' })).toBeVisible();

  const mobileAiButton = page.getByRole('button', { name: 'AI 빠른 실행' });
  await mobileAiButton.click();
  await expect(page.getByRole('dialog', { name: 'AI 빠른 실행 메뉴' })).toBeVisible();
  await expect(page.getByRole('button', { name: '답장 초안' })).toBeVisible();
  await page.getByRole('link', { name: '더보기' }).click();
  await expect(page.getByRole('region', { name: '모바일 AI 실행' })).toBeVisible();
  await expect(page.getByRole('heading', { name: '관계 맥락' })).toBeVisible();

  await page.getByRole('link', { name: '맥락 검색' }).click();
  await expect(page.getByRole('region', { name: '모바일 맥락 검색' })).toBeVisible();
  await expect(page.getByText('메일, 첨부, 일정, 사람을 한 번에 검색합니다.')).toBeVisible();

  await page.getByRole('link', { name: '일정' }).click();
  await expect(page.getByRole('region', { name: '모바일 일정 연결' })).toBeVisible();
  await expect(page.getByText('캘린더 반영 대기')).toBeVisible();
});

const responsiveViewports = [
  { name: 'short mobile', width: 390, height: 640 },
  { name: 'mobile', width: 390, height: 844 },
  { name: 'tablet portrait', width: 768, height: 1024 },
  { name: 'tablet landscape', width: 1024, height: 768 },
  { name: 'desktop', width: 1280, height: 1024 },
  { name: 'wide desktop', width: 1920, height: 1080 },
] as const;

for (const viewport of responsiveViewports) {
  test(`keeps the branded workspace usable without horizontal overflow at ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await mockDashboardApi(page);

    await page.goto('/');

    await expect(page.locator('main#main-content')).toBeVisible();
    await expect(page.locator('header[aria-label="Naruon workspace header"]')).toBeVisible();
    await expect(page.getByRole('region', { name: '홈 개요 대시보드' }).first()).toBeVisible();
    if (viewport.width <= 390) {
      const metricLabel = page
        .getByRole('article', { name: '받은 메일' })
        .first()
        .getByText('받은 메일', { exact: true });
      await expect(metricLabel).toBeVisible();
      const metricLabelBox = await metricLabel.boundingBox();
      expect(metricLabelBox).not.toBeNull();
      if (!metricLabelBox) throw new Error('Metric label bounding box was unavailable.');
      expect(metricLabelBox.height).toBeLessThan(48);
    }
    await page.getByRole('button', { name: '메일함 바로가기' }).first().click();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);

    if (viewport.width < 1024) {
      await expect(page.getByRole('navigation', { name: 'Mobile workspace sections' })).toBeVisible();
      await expect(page.getByRole('button', { name: '워크스페이스 메뉴 열기' })).toBeVisible();
      await expect(page.getByRole('region', { name: '모바일 받은편지함' })).toBeVisible();
    } else if (viewport.width < 1280) {
      await expect(page.getByRole('button', { name: '워크스페이스 메뉴 열기' })).toBeVisible();
      await page.getByRole('button', { name: '워크스페이스 메뉴 열기' }).click();
      const menu = page.getByRole('dialog', { name: '모바일 워크스페이스 메뉴' });
      await expect(menu.getByRole('link', { name: '메일', exact: true })).toHaveAttribute('href', '/mail');
      await expect(menu.getByRole('link', { name: /보낸 메일/ })).toHaveAttribute('href', '/mail?folder=sent');
      await expect(menu.getByRole('link', { name: '맥락 검색', exact: true })).toHaveAttribute('href', '/search');
      await menu.getByRole('button', { name: '모바일 워크스페이스 메뉴 닫기' }).click();
      await expect(page.getByRole('region', { name: '태블릿 메일 작업공간' })).toBeVisible();
      await expect(page.getByRole('region', { name: '데스크톱 메일 작업공간' })).toBeHidden();
      await expect(page.getByText('태블릿 맥락 패널')).toBeVisible();
      await expect(page.getByRole('button', { name: '캘린더 반영' })).toBeVisible();
      await expect(page.getByRole('button', { name: '답장 초안' })).toBeVisible();
      await expect(page.getByRole('button', { name: '할 일 만들기' })).toBeVisible();
    } else {
      await expect(page.getByRole('navigation', { name: 'Primary workspace navigation' })).toBeVisible();
      await expect(page.getByRole('region', { name: '데스크톱 메일 작업공간' })).toBeVisible();
    }
  });
}

for (const destination of [
  { path: '/mail', heading: '메일을 선택하세요', marker: { name: '받은편지함' } },
  { path: '/calendar', heading: '일정 관리', marker: { text: 'CalDAV/CardDAV/WebDAV writeback intent' } },
  { path: '/tasks', heading: '할 일 추적', marker: { name: '리소스 배정 검토 회의' } },
  { path: '/data', heading: '데이터와 파일', marker: { text: '중복 반입과 thread 정리' } },
  { path: '/search', heading: '맥락 검색', marker: { name: '관계 그래프와 타임라인' } },
  { path: '/security', heading: '보안과 관리자', marker: { text: '관리자 경계' } },
  { path: '/projects', heading: '프로젝트 워크스페이스', marker: { name: '의사결정 로그' } },
  { path: '/ai-hub', heading: 'AI 허브', marker: { name: '실행 항목' } },
  { path: '/settings', heading: '설정 (Settings)', marker: { text: 'Self-hosted Runner' } },
] as const) {
  test(`renders the ${destination.path} workspace destination without horizontal overflow`, async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 1024 });
    await mockDashboardApi(page);

    await page.goto(destination.path);

    await expect(page.getByRole('heading', { name: destination.heading })).toBeVisible();
    if ('name' in destination.marker) {
      await expect(page.getByRole('heading', { name: destination.marker.name }).first()).toBeVisible();
    } else {
      await expect(page.getByText(destination.marker.text)).toBeVisible();
    }
    await expect(page.getByRole('navigation', { name: 'Primary workspace navigation' })).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
}

test('renders sent mail reply tracking route with signed API headers', async ({ page }, testInfo) => {
  const expectedNaruonToken = 'signed-sent-mail-e2e-token';
  const publicIdentityHeaders = [
    'x-user-id',
    'x-organization-id',
    'x-group-id',
    'x-group-ids',
    'x-user-role',
    'x-dev-auth-token',
  ];
  await page.setViewportSize({ width: 1280, height: 1024 });
  await mockDashboardApi(page);
  await page.addInitScript((token) => {
    window.localStorage.setItem('naruon_session_token', token);
  }, expectedNaruonToken);

  const sentRequest = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return url.pathname === '/api/emails' && url.searchParams.get('folder') === 'sent' && request.method() === 'GET';
  });

  await page.goto('/mail?folder=sent');
  const requestHeaders = (await sentRequest).headers();
  expect(requestHeaders.authorization).toBe(`Bearer ${expectedNaruonToken}`);
  for (const headerName of publicIdentityHeaders) {
    expect(requestHeaders[headerName]).toBeUndefined();
  }

  await expect(page.getByRole('heading', { name: '보낸 메일' }).first()).toBeVisible();
  await expect(page.getByText('답변 대기').first()).toBeVisible();
  await expect(page.getByText('응답 대기 중').first()).toBeVisible();
  await expect(page.getByText('지식 정리').first()).toBeVisible();
  await expect(page.getByText('벤더 계약 답변 요청').first()).toBeVisible();
  const desktopOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(desktopOverflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('sent-mail-reply-tracking-desktop.png'), fullPage: false });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/mail?folder=sent');
  await expect(page.getByRole('heading', { name: '보낸 메일' }).first()).toBeVisible();
  await expect(page.getByText('응답 대기 중').first()).toBeVisible();
  await expect(page.getByText('나에게 보낸 지식 메모').first()).toBeVisible();
  const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(mobileOverflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('sent-mail-reply-tracking-mobile.png'), fullPage: false });
  const sentScrollMetrics = await page.locator('#mobile-inbox [data-slot="scroll-area-viewport"]').evaluate((scroller) => {
    scroller.scrollTop = 0;
    const before = scroller.scrollTop;
    scroller.scrollTop = scroller.scrollHeight;
    return {
      before,
      after: scroller.scrollTop,
      maxScroll: scroller.scrollHeight - scroller.clientHeight,
    };
  });
  expect(sentScrollMetrics.maxScroll).toBeGreaterThan(0);
  expect(sentScrollMetrics.after).toBeGreaterThan(sentScrollMetrics.before);
  await page.screenshot({ path: testInfo.outputPath('sent-mail-reply-tracking-mobile-scroll.png'), fullPage: false });
});

test('renders the settings self-hosted connector manifest with mobile scrolling', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockDashboardApi(page);

  await page.goto('/settings');
  await page.getByRole('button', { name: '개발자' }).first().click();

  await expect(page.getByText('Self-hosted connector manifest')).toBeVisible();
  await expect(page.getByText('Naruon은 이메일 서버가 아닙니다')).toBeVisible();
  await expect(page.getByText('naruon.net', { exact: true })).toBeVisible();
  await expect(page.getByText('ci_smoke_only')).toBeVisible();
  await expect(page.getByText('smtp_server')).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('settings-runner-mobile-manifest.png'), fullPage: false });

  const scrollMetrics = await page.evaluate(() => {
    const scroller = Array.from(document.querySelectorAll('body, body *')).find((element) => {
      const style = window.getComputedStyle(element);
      return style.overflowY !== 'hidden' && element.scrollHeight > element.clientHeight + 10;
    });
    if (!scroller) return null;
    const before = scroller.scrollTop;
    scroller.scrollTop = scroller.scrollHeight;
    return {
      before,
      after: scroller.scrollTop,
      maxScroll: scroller.scrollHeight - scroller.clientHeight,
    };
  });
  expect(scrollMetrics).not.toBeNull();
  expect(scrollMetrics?.maxScroll).toBeGreaterThan(0);
  expect(scrollMetrics?.after).toBeGreaterThan(scrollMetrics?.before ?? 0);
  await page.screenshot({ path: testInfo.outputPath('settings-runner-mobile-scroll.png'), fullPage: false });
});

test('renders calendar writeback intent status without direct provider writes', async ({ page }, testInfo) => {
  const expectedNaruonToken = 'signed-calendar-e2e-token';
  const publicIdentityHeaders = [
    'x-user-id',
    'x-organization-id',
    'x-group-id',
    'x-group-ids',
    'x-user-role',
    'x-dev-auth-token',
  ];
  await page.setViewportSize({ width: 1280, height: 1024 });
  await mockDashboardApi(page);
  await page.addInitScript((token) => {
    window.localStorage.setItem('naruon_session_token', token);
  }, expectedNaruonToken);

  await page.goto('/calendar');
  const desktopWritebackRequest = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return url.pathname === '/api/calendar/writeback-intent' && request.method() === 'POST';
  });
  await page.getByRole('button', { name: '새 일정 intent 점검' }).click();
  const desktopRequestHeaders = (await desktopWritebackRequest).headers();
  expect(desktopRequestHeaders.authorization).toBe(`Bearer ${expectedNaruonToken}`);
  for (const headerName of publicIdentityHeaders) {
    expect(desktopRequestHeaders[headerName]).toBeUndefined();
  }

  await expect(page.getByText('customer_owned')).toBeVisible();
  await expect(page.getByText('caldav', { exact: true })).toBeVisible();
  await expect(page.getByText('caldav-primary')).toBeVisible();
  await expect(page.getByText('calendar.writeback_intent.created')).toBeVisible();
  await expect(page.getByText('동기화 완료')).toHaveCount(0);
  const desktopOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(desktopOverflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('calendar-writeback-intent-desktop.png'), fullPage: false });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/calendar');
  await expect(page.getByRole('heading', { name: '일정 관리' })).toBeVisible();
  const mobileWritebackRequest = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return url.pathname === '/api/calendar/writeback-intent' && request.method() === 'POST';
  });
  await page.getByRole('button', { name: '새 일정 intent 점검' }).click();
  const mobileRequestHeaders = (await mobileWritebackRequest).headers();
  expect(mobileRequestHeaders.authorization).toBe(`Bearer ${expectedNaruonToken}`);
  for (const headerName of publicIdentityHeaders) {
    expect(mobileRequestHeaders[headerName]).toBeUndefined();
  }
  await expect(page.getByText('customer_owned')).toBeVisible();
  const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(mobileOverflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('calendar-writeback-intent-mobile.png'), fullPage: false });
  const calendarScrollMetrics = await page.evaluate(() => {
    const scroller = Array.from(document.querySelectorAll('main div')).find((element) => {
      const style = window.getComputedStyle(element);
      return style.overflowY !== 'hidden' && element.scrollHeight > element.clientHeight + 10;
    });
    if (!scroller) return null;
    const before = scroller.scrollTop;
    scroller.scrollTop = scroller.scrollHeight;
    return {
      before,
      after: scroller.scrollTop,
      maxScroll: scroller.scrollHeight - scroller.clientHeight,
    };
  });
  expect(calendarScrollMetrics).not.toBeNull();
  expect(calendarScrollMetrics?.maxScroll).toBeGreaterThan(0);
  expect(calendarScrollMetrics?.after).toBeGreaterThan(calendarScrollMetrics?.before ?? 0);
  await page.screenshot({ path: testInfo.outputPath('calendar-writeback-intent-mobile-scroll.png'), fullPage: false });
});

test('renders data WebDAV writeback intent status without direct provider writes', async ({ page }, testInfo) => {
  const expectedNaruonToken = 'signed-webdav-e2e-token';
  const publicIdentityHeaders = [
    'x-user-id',
    'x-organization-id',
    'x-group-id',
    'x-group-ids',
    'x-user-role',
    'x-dev-auth-token',
  ];
  await page.setViewportSize({ width: 1280, height: 1024 });
  await mockDashboardApi(page);
  await page.addInitScript((token) => {
    window.localStorage.setItem('naruon_session_token', token);
  }, expectedNaruonToken);

  await page.goto('/data');
  const desktopWritebackRequest = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return url.pathname === '/api/webdav/writeback-intent' && request.method() === 'POST';
  });
  await page.getByRole('button', { name: 'WebDAV intent 승인 점검' }).click();
  const desktopHeaders = (await desktopWritebackRequest).headers();
  expect(desktopHeaders.authorization).toBe(`Bearer ${expectedNaruonToken}`);
  for (const headerName of publicIdentityHeaders) {
    expect(desktopHeaders[headerName]).toBeUndefined();
  }

  await expect(page.getByText('writeback', { exact: true })).toBeVisible();
  await expect(page.getByText('server-authoritative')).toBeVisible();
  await expect(page.getByText('https://webdav.naruon.net').first()).toBeVisible();
  await expect(page.getByText('required', { exact: true })).toBeVisible();
  const desktopOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(desktopOverflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('data-webdav-writeback-intent-desktop.png'), fullPage: false });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/data');
  await expect(page.getByRole('heading', { name: '데이터와 파일' })).toBeVisible();
  const mobileWritebackRequest = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return url.pathname === '/api/webdav/writeback-intent' && request.method() === 'POST';
  });
  await page.getByRole('button', { name: 'WebDAV intent 승인 점검' }).click();
  const mobileHeaders = (await mobileWritebackRequest).headers();
  expect(mobileHeaders.authorization).toBe(`Bearer ${expectedNaruonToken}`);
  for (const headerName of publicIdentityHeaders) {
    expect(mobileHeaders[headerName]).toBeUndefined();
  }
  await expect(page.getByText('server-authoritative')).toBeVisible();
  await page.getByText('server-authoritative').scrollIntoViewIfNeeded();
  await page.mouse.wheel(0, 140);
  const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(mobileOverflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('data-webdav-writeback-intent-mobile.png'), fullPage: false });
  const dataScrollMetrics = await page.evaluate(() => {
    const scroller = Array.from(document.querySelectorAll('main, main *')).find((element) => {
      const style = window.getComputedStyle(element);
      return style.overflowY !== 'hidden' && element.scrollHeight > element.clientHeight + 10;
    });
    if (!scroller) return null;
    const before = scroller.scrollTop;
    scroller.scrollTop = scroller.scrollHeight;
    return {
      before,
      after: scroller.scrollTop,
      maxScroll: scroller.scrollHeight - scroller.clientHeight,
    };
  });
  expect(dataScrollMetrics).not.toBeNull();
  expect(dataScrollMetrics?.maxScroll).toBeGreaterThan(0);
  expect(dataScrollMetrics?.after).toBeGreaterThan(dataScrollMetrics?.before ?? 0);
  await page.screenshot({ path: testInfo.outputPath('data-webdav-writeback-intent-mobile-scroll.png'), fullPage: false });
});

test('renders API-backed context search sender DAG and reply tracking', async ({ page }, testInfo) => {
  const expectedNaruonToken = 'signed-search-e2e-token';
  const publicIdentityHeaders = [
    'x-user-id',
    'x-organization-id',
    'x-group-id',
    'x-group-ids',
    'x-user-role',
    'x-dev-auth-token',
  ];
  await page.setViewportSize({ width: 1280, height: 1024 });
  await mockDashboardApi(page);
  await page.addInitScript((token) => {
    window.localStorage.setItem('naruon_session_token', token);
  }, expectedNaruonToken);

  const searchRequest = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return url.pathname === '/api/search' && request.method() === 'POST';
  });
  const graphRequest = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return url.pathname === '/api/network/graph' && request.method() === 'GET';
  });

  await page.goto('/search');
  const searchHeaders = (await searchRequest).headers();
  const graphHeaders = (await graphRequest).headers();
  expect(searchHeaders.authorization).toBe(`Bearer ${expectedNaruonToken}`);
  expect(graphHeaders.authorization).toBe(`Bearer ${expectedNaruonToken}`);
  for (const headerName of publicIdentityHeaders) {
    expect(searchHeaders[headerName]).toBeUndefined();
    expect(graphHeaders[headerName]).toBeUndefined();
  }

  await expect(page.getByRole('heading', { name: '맥락 검색' })).toBeAttached();
  await expect(page.getByRole('heading', { name: 'Q2 출시 계획 및 우선순위 조정' }).first()).toBeVisible();
  await expect(page.getByText('thread-q2').first()).toBeVisible();
  await expect(page.getByText('답장 2건').first()).toBeVisible();
  await expect(page.getByText('관계 그래프와 타임라인')).toBeVisible();
  await expect(page.getByText('김지현 PM').first()).toBeVisible();
  const desktopOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(desktopOverflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('search-dag-reply-desktop.png'), fullPage: false });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/search');
  await expect(page.getByRole('heading', { name: 'Q2 출시 계획 및 우선순위 조정' }).first()).toBeVisible();
  await expect(page.getByText('thread-q2').first()).toBeVisible();
  const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(mobileOverflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath('search-dag-reply-mobile.png'), fullPage: false });
  const resultScrollMetrics = await page.locator('aside').evaluate((scroller) => {
    const before = scroller.scrollTop;
    scroller.scrollTop = scroller.scrollHeight;
    return {
      before,
      after: scroller.scrollTop,
      maxScroll: scroller.scrollHeight - scroller.clientHeight,
    };
  });
  expect(resultScrollMetrics.maxScroll).toBeGreaterThan(0);
  expect(resultScrollMetrics.after).toBeGreaterThan(resultScrollMetrics.before);

  const detailScrollMetrics = await page.locator('main main').evaluate((scroller) => {
    const before = scroller.scrollTop;
    scroller.scrollTop = scroller.scrollHeight;
    return {
      before,
      after: scroller.scrollTop,
      maxScroll: scroller.scrollHeight - scroller.clientHeight,
    };
  });
  expect(detailScrollMetrics.maxScroll).toBeGreaterThan(0);
  expect(detailScrollMetrics.after).toBeGreaterThan(detailScrollMetrics.before);
  await page.getByText('관계 이해').scrollIntoViewIfNeeded();
  await expect(page.getByText('관계 이해')).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('search-dag-reply-mobile-scroll.png'), fullPage: false });
});

test('captures responsive startup evidence for desktop tablet mobile and the mobile drawer', async ({ page }, testInfo) => {
  await mockDashboardApi(page);
  for (const viewport of [
    { name: 'desktop', width: 1280, height: 1024 },
    { name: 'tablet', width: 1024, height: 768 },
    { name: 'mobile', width: 390, height: 844 },
  ] as const) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto('/');
    await expect(page.getByRole('region', { name: '홈 개요 대시보드' }).first()).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath(`startup-${viewport.name}.png`), fullPage: true });
    if (viewport.name === 'mobile') {
      await page.getByRole('button', { name: '워크스페이스 메뉴 열기' }).click();
      await expect(page.getByRole('dialog', { name: '모바일 워크스페이스 메뉴' })).toBeVisible();
      await page.screenshot({ path: testInfo.outputPath('startup-mobile-drawer.png'), fullPage: true });
    }
  }
});

test('validates mobile hamburger composition and startup preference controls', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockDashboardApi(page);

  await page.goto('/');
  await page.getByRole('button', { name: '워크스페이스 메뉴 열기' }).click();

  const menu = page.locator('#mobile-workspace-menu');
  const menuWidth = await menu.evaluate((element) => element.getBoundingClientRect().width);
  expect(menuWidth).toBeGreaterThanOrEqual(340);
  await expect(menu.getByText('시작 화면', { exact: true })).toBeVisible();
  await expect(menu.getByRole('button', { name: '대시보드' })).toBeVisible();
  await expect(menu.getByRole('button', { name: '이메일' })).toBeVisible();
  await expect(menu.getByRole('button', { name: '일정' })).toBeVisible();
  await expect(menu.getByRole('link', { name: '홈', exact: true })).toHaveAttribute('href', '/');
  await expect(menu.getByRole('link', { name: '메일', exact: true })).toHaveAttribute('href', '/mail');
  await expect(menu.getByRole('link', { name: /보낸 메일/ })).toHaveAttribute('href', '/mail?folder=sent');
  await expect(menu.getByRole('link', { name: '일정', exact: true })).toHaveAttribute('href', '/calendar');
  await expect(menu.getByRole('link', { name: '맥락 검색', exact: true })).toHaveAttribute('href', '/search');
  await expect(menu.getByRole('link', { name: 'AI 허브', exact: true })).toHaveAttribute('href', '/ai-hub');
  await expect(menu.getByText('워크스페이스', { exact: true })).toBeVisible();
  await expect(menu.getByText('주요 작업공간', { exact: true })).toBeVisible();
  await expect(menu.getByText('도움', { exact: true })).toBeVisible();
  await expect(menu.getByRole('link', { name: '작업', exact: true })).toHaveAttribute('href', '/tasks');
  await expect(menu.getByRole('link', { name: '프로젝트', exact: true })).toHaveAttribute('href', '/projects');
  await expect(menu.getByRole('link', { name: '데이터', exact: true })).toHaveAttribute('href', '/data');
  await expect(menu.getByRole('link', { name: '보안', exact: true })).toHaveAttribute('href', '/security');
  await expect(menu.getByRole('link', { name: '설정', exact: true })).toHaveAttribute('href', '/settings');
  await expect(menu.getByRole('link', { name: '도움말', exact: true })).toHaveAttribute('href', '/settings#help');
  await expect(menu.getByRole('link', { name: '프로필', exact: true })).toHaveAttribute('href', '/settings#profile');
  const desktopDestinationHrefs = await page
    .locator('nav[aria-label="Primary workspace navigation"] a')
    .evaluateAll((links) => links.map((link) => link.getAttribute('href')));
  const mobileDestinationHrefs = await menu
    .locator('nav[aria-label="Mobile primary destinations"] a')
    .evaluateAll((links) => links.map((link) => link.getAttribute('href')));
  expect(mobileDestinationHrefs).toEqual(desktopDestinationHrefs);
  await expect(menu.getByRole('link', { name: /일정 연결/ })).toHaveAttribute('href', '#mobile-calendar');
  await expect(menu.getByText(/중요 메일.*준비 중/)).toHaveCount(0);
  await menu.evaluate((element) => {
    element.scrollTop = element.scrollHeight;
  });
  await expect(menu.getByText('도움말')).toBeVisible();
  await expect(menu.getByText('프로필')).toBeVisible();
  const utilityGap = await menu.getByText('프로필').evaluate((element) => {
    const item = element.getBoundingClientRect();
    const dialog = document.querySelector('#mobile-workspace-menu')?.getBoundingClientRect();
    return dialog ? dialog.bottom - item.bottom : 0;
  });
  expect(utilityGap).toBeGreaterThanOrEqual(0);
  await page.screenshot({ path: testInfo.outputPath('mobile-workspace-menu.png'), fullPage: true });

  await menu.getByRole('button', { name: '일정' }).click();
  await expect(page.getByRole('button', { name: '워크스페이스 메뉴 열기' })).toHaveAttribute('aria-expanded', 'false');
  await expect(menu.getByText('시작 화면', { exact: true })).toBeHidden();
});

for (const viewport of [
  { name: 'mobile', width: 390, height: 844 },
  { name: 'desktop', width: 1280, height: 1024 },
] as const) {
  test(`renders the functional AI hub sections without horizontal overflow at ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await mockDashboardApi(page);

    await page.goto('/ai-hub');

    await expect(page.getByRole('heading', { name: 'AI 허브' })).toBeVisible();
    await expect(page.getByRole('region', { name: '맥락 종합' })).toBeVisible();
    await expect(page.getByRole('region', { name: '판단 포인트' })).toBeVisible();
    await expect(page.getByRole('region', { name: '실행 항목' })).toBeVisible();
    await expect(page.getByText('최근 AI 요약')).toHaveCount(0);
    await expect(page.getByText('설명 없음')).toHaveCount(0);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
}

for (const section of [
  { hash: 'context', linkName: /맥락 종합/, region: '맥락 종합' },
  { hash: 'decisions', linkName: /판단 포인트/, region: '판단 포인트' },
  { hash: 'actions', linkName: /실행 항목/, region: '실행 항목' },
] as const) {
  test(`deep-links the AI hub execution checkpoint to ${section.region}`, async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 1024 });
    await mockDashboardApi(page);

    await page.goto('/ai-hub');
    await page
      .getByRole('navigation', { name: 'AI hub execution checkpoints' })
      .getByRole('link', { name: section.linkName })
      .click();

    await expect(page).toHaveURL(new RegExp(`/ai-hub#${section.hash}$`));
    await expect(page.getByRole('region', { name: section.region })).toBeVisible();
    const targetTop = await page.getByRole('region', { name: section.region }).evaluate((element) => Math.round(element.getBoundingClientRect().top));
    expect(targetTop).toBeGreaterThanOrEqual(0);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
}

for (const panel of [
  { hash: 'mobile-inbox', region: '모바일 받은편지함', finalText: 'Q2 출시 계획 및 우선순위 조정', oldPlaceholder: '사람 결과 준비 중' },
  { hash: 'mobile-search', region: '모바일 맥락 검색', finalText: '강민수 의사결정 메모', oldPlaceholder: '사람 결과 준비 중' },
  { hash: 'mobile-calendar', region: '모바일 일정 연결', finalText: '파트너 미팅 일정 확정', oldPlaceholder: '디자인 리뷰 후속 조치' },
] as const) {
  test(`allows short mobile users to scroll the ${panel.region} panel past the bottom nav`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 640 });
    await mockDashboardApi(page);

    await page.goto(`/#${panel.hash}`);

    const region = page.getByRole('region', { name: panel.region });
    await expect(region).toBeVisible();
    await expect(region.getByText(panel.oldPlaceholder)).toHaveCount(0);
    await expect(region.getByText(panel.finalText)).toBeVisible();
    await region.evaluate((element) => {
      element.scrollTop = element.scrollHeight;
    });
    const bottomGap = await region.getByText(panel.finalText).evaluate((element) => {
      const item = element.getBoundingClientRect();
      const nav = document.querySelector('nav[aria-label="Mobile workspace sections"]')?.getBoundingClientRect();
      return nav ? nav.top - item.bottom : 0;
    });
    expect(bottomGap).toBeGreaterThanOrEqual(0);
  });
}

test('keeps selected mobile email detail and actions above the bottom navigation', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 640 });
  await mockDashboardApi(page);

  await page.goto('/');
  await page.getByRole('button', { name: '메일함 바로가기' }).first().click();
  await page.getByRole('button', { name: /김지현 PM/ }).click();

  const detailRegion = page.getByRole('region', { name: '모바일 메일 상세' });
  await expect(detailRegion).toBeVisible();
  await expect(detailRegion.getByText('Q2 출시 계획 및 우선순위 조정')).toBeVisible();
  await expect(detailRegion.getByText('출시 일정, 마케팅 계획, 파트너 미팅')).toBeVisible();
  await expect(detailRegion.getByRole('button', { name: '할 일 만들기' })).toBeVisible();

  const replyButton = detailRegion.getByRole('button', { name: '답장 보내기' });
  await replyButton.scrollIntoViewIfNeeded();
  const bottomGap = await replyButton.evaluate((element) => {
    const item = element.getBoundingClientRect();
    const nav = document.querySelector('nav[aria-label="Mobile workspace sections"]')?.getBoundingClientRect();
    return nav ? nav.top - item.bottom : 0;
  });
  expect(bottomGap).toBeGreaterThanOrEqual(0);

  await page.getByRole('button', { name: 'AI 빠른 실행' }).click();
  await page.getByRole('dialog', { name: 'AI 빠른 실행 메뉴' }).getByRole('button', { name: '할 일 만들기' }).click();
  await expect(detailRegion.getByText('2개 실행 항목을 티켓형 할 일로 추적합니다.')).toBeVisible();
});
