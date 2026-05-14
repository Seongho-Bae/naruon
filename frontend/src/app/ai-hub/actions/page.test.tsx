/* @vitest-environment jsdom */
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';

const apiClientMock = vi.hoisted(() => ({
  getBearerToken: vi.fn(() => null),
  getCurrentUserId: vi.fn(() => 'testuser'),
  getCurrentOrganizationId: vi.fn(() => 'org-local-dev'),
  get: vi.fn(async (endpoint: string) => {
    if (endpoint === '/api/mailbox-accounts') {
      return {
        items: [
          {
            id: 2,
            email_address: 'beta@example.com',
            display_name: 'Beta',
            is_default_reply: false,
            is_active: true,
          },
        ],
      };
    }
    return {
      emails: [
        {
          id: 7,
          subject: '출시 일정 검토 요청',
          snippet: 'Q2 출시 계획과 우선순위 조정 요청입니다.',
          unread: true,
          reply_count: 3,
        },
      ],
    };
  }),
}));

vi.mock('@/lib/api-client', () => ({ apiClient: apiClientMock }));

import AIHubActionsPage from './page';

async function flushAsyncWork() {
  for (let index = 0; index < 5; index += 1) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

describe('AIHubActionsPage', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    window.localStorage.clear();
    vi.clearAllMocks();
  });

  it('does not duplicate queued email items in the backlog list', async () => {
    window.localStorage.setItem('naruon.executionQueue.org-local-dev.testuser', JSON.stringify([
      {
        id: 70,
        sourceMailboxAccountId: 2,
        sourceEmailId: 7,
        sourceSnippet: 'Q2 출시 계획과 우선순위 조정 요청입니다.',
        title: '출시 일정 검토 요청',
        sender: '김지현 PM',
        status: 'queued',
        createdAt: '2026-05-14T00:00:00.000Z',
        updatedAt: '2026-05-14T00:00:00.000Z',
        completedAt: null,
      },
    ]));

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<AIHubActionsPage />);
    });
    await flushAsyncWork();

    const matches = container.textContent?.match(/출시 일정 검토 요청/g) ?? [];
    expect(matches).toHaveLength(1);
    expect(container.textContent).toContain('스와이프로 담긴 실행 항목');
    expect(container.textContent).toContain('Beta');
    expect(container.textContent).toContain('Q2 출시 계획과 우선순위 조정 요청입니다.');
  });
});
