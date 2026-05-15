/* @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from 'vitest';

import { listExecutionQueue, queueEmailExecutionItem, markExecutionQueueItemDone } from './execution-queue';

function createUnsignedToken(payload: Record<string, unknown>) {
  const encoded = window.btoa(JSON.stringify(payload)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  return `header.${encoded}.signature`;
}

function jsonResponse(body: unknown) {
  return {
    ok: true,
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

describe('execution queue', () => {
  afterEach(() => {
    window.localStorage.clear();
    vi.unstubAllGlobals();
  });

  it('adds email-derived execution items once without duplicating the queue entry', async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/api/execution-items/from-email')) {
        return jsonResponse({
          item: {
            id: 70,
            user_id: 'testuser',
            source_mailbox_account_id: 2,
            source_email_id: 7,
            source_thread_id: 'thread-q2',
            source_message_id: '<q2@example.com>',
            source_snippet: 'Q2 출시 계획 및 우선순위 조정 요청입니다.',
            title: '출시 일정 검토 요청',
            sender: 'owner@example.com',
            status: 'queued',
            created_at: '2026-05-14T00:00:00.000Z',
            updated_at: '2026-05-14T00:00:00.000Z',
            completed_at: null,
          },
        });
      }
      throw new Error(`Unexpected ${init?.method || 'GET'} ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await queueEmailExecutionItem({ id: 7, subject: '출시 일정 검토 요청', sender: 'owner@example.com' });
    await queueEmailExecutionItem({ id: 7, subject: '출시 일정 검토 요청', sender: 'owner@example.com' });

    const items = listExecutionQueue();
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({ id: 70, sourceMailboxAccountId: 2, sourceEmailId: 7, sourceSnippet: 'Q2 출시 계획 및 우선순위 조정 요청입니다.', title: '출시 일정 검토 요청', status: 'queued' });
  });

  it('marks queued items as done when the opposite swipe action completes them', async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/api/execution-items/from-email')) {
        return jsonResponse({
          item: {
            id: 80,
            user_id: 'testuser',
            source_mailbox_account_id: 2,
            source_email_id: 8,
            source_thread_id: 'thread-8',
            source_message_id: '<mail-8@example.com>',
            source_snippet: '회의 일정 확인 메일입니다.',
            title: '회의 일정 확인',
            sender: 'pm@example.com',
            status: 'queued',
            created_at: '2026-05-14T00:00:00.000Z',
            updated_at: '2026-05-14T00:00:00.000Z',
            completed_at: null,
          },
        });
      }
      if (url.endsWith('/api/execution-items/80') && init?.method === 'PATCH') {
        return jsonResponse({
          item: {
            id: 80,
            user_id: 'testuser',
            source_mailbox_account_id: 2,
            source_email_id: 8,
            source_thread_id: 'thread-8',
            source_message_id: '<mail-8@example.com>',
            source_snippet: '회의 일정 확인 메일입니다.',
            title: '회의 일정 확인',
            sender: 'pm@example.com',
            status: 'done',
            created_at: '2026-05-14T00:00:00.000Z',
            updated_at: '2026-05-14T00:05:00.000Z',
            completed_at: '2026-05-14T00:05:00.000Z',
          },
        });
      }
      throw new Error(`Unexpected ${init?.method || 'GET'} ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await queueEmailExecutionItem({ id: 8, subject: '회의 일정 확인', sender: 'pm@example.com' });

    const updated = await markExecutionQueueItemDone(8);

    expect(updated).toMatchObject({ id: 80, sourceEmailId: 8, status: 'done' });
    expect(listExecutionQueue()[0].status).toBe('done');
  });

  it('uses a user-scoped cache key so one local session does not read another user cache', async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith('/api/execution-items/from-email')) {
        return jsonResponse({
          item: {
            id: 90,
            user_id: 'admin',
            source_mailbox_account_id: 3,
            source_email_id: 9,
            source_thread_id: 'thread-9',
            source_message_id: '<mail-9@example.com>',
            source_snippet: '관리자 작업 근거 메일입니다.',
            title: '관리자 작업',
            sender: 'admin@example.com',
            status: 'queued',
            created_at: '2026-05-14T00:00:00.000Z',
            updated_at: '2026-05-14T00:00:00.000Z',
            completed_at: null,
          },
        });
      }
      throw new Error(`Unexpected ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('http://localhost/settings'),
    });

    window.localStorage.setItem('naruon.dev_user', 'unused');
    window.localStorage.setItem('naruon_dev_user', 'admin');
    await queueEmailExecutionItem({ id: 9, subject: '관리자 작업', sender: 'admin@example.com' });
    expect(window.localStorage.getItem('naruon.executionQueue.org-local-dev.admin') || '').toContain('관리자 작업');

    window.localStorage.setItem('naruon_dev_user', 'testuser');
    expect(listExecutionQueue()).toEqual([]);
  });

  it('does not read persisted local cache when a bearer-token session is active', () => {
    window.localStorage.setItem('naruon.executionQueue.org-local-dev.admin', JSON.stringify([
      {
        id: 70,
        sourceEmailId: 7,
        sourceThreadId: 'thread-q2',
        sourceMessageId: '<q2@example.com>',
        title: '출시 일정 검토 요청',
        sender: 'owner@example.com',
        status: 'queued',
        createdAt: '2026-05-14T00:00:00.000Z',
        updatedAt: '2026-05-14T00:00:00.000Z',
        completedAt: null,
      },
    ]));
    window.localStorage.setItem('naruon_bearer_token', createUnsignedToken({ sub: 'admin', organization_id: 'org-acme', exp: Math.floor(Date.now() / 1000) + 300 }));

    expect(listExecutionQueue()).toEqual([]);
  });
});
