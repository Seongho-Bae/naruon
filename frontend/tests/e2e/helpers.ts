import type { Page, Route } from '@playwright/test';

const email = {
  id: 7,
  message_id: '<q2@example.com>',
  thread_id: 'thread-q2',
  sender: '김지현 PM',
  recipients: 'user@naruon.ai',
  reply_to: 'jihyun@naruon.ai',
  subject: 'Q2 출시 계획 및 우선순위 조정',
  date: '2026-05-11T09:30:00Z',
  body: 'Q2 출시 일정과 마케팅 계획을 우선순위 기준으로 재정렬해 보았습니다.',
  snippet: 'Q2 출시 계획과 우선순위 조정 요청입니다.',
  unread: true,
  reply_count: 2,
};

const sibling = {
  ...email,
  id: 8,
  message_id: '<q2-reply@example.com>',
  body: '파트너 미팅 전까지 일정 확인이 필요합니다.',
};

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type, X-User-Id',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    },
    body: JSON.stringify(body),
  });
}

export async function mockDashboardApi(page: Page) {
  await page.route('**/api/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    if (request.method() === 'OPTIONS') {
      await route.fulfill({
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type, X-User-Id',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        },
      });
      return;
    }

    if (path === '/api/emails' && request.method() === 'GET') {
      await fulfillJson(route, { emails: [email] });
      return;
    }

    if (path === '/api/search' && request.method() === 'POST') {
      await fulfillJson(route, { results: [email] });
      return;
    }

    if (path === '/api/emails/7') {
      await fulfillJson(route, email);
      return;
    }

    if (path === '/api/emails/thread/thread-q2') {
      await fulfillJson(route, { thread: [email, sibling] });
      return;
    }

    if (path === '/api/llm/summarize') {
      await fulfillJson(route, {
        summary: '출시 일정, 마케팅 계획, 파트너 미팅을 하나의 실행 흐름으로 정리해야 합니다.',
        todos: ['리소스 배정 검토 회의', '마케팅 캠페인 오프'],
      });
      return;
    }

    if (path === '/api/llm/draft') {
      await fulfillJson(route, { draft: '검토 후 일정과 우선순위를 정리해 공유드리겠습니다.' });
      return;
    }

    if (path === '/api/emails/send') {
      await fulfillJson(route, { simulated: true });
      return;
    }

    if (path === '/api/calendar/sync') {
      await fulfillJson(route, { synced: 2 });
      return;
    }

    if (path === '/api/network/graph') {
      await fulfillJson(route, {
        nodes: [{ id: 'person-1', label: '김지현', title: 'PM' }],
        edges: [{ from: 'person-1', to: 'person-1', title: '관련 메일' }],
      });
      return;
    }

    await route.fulfill({ status: 404, body: 'Not mocked' });
  });
}
