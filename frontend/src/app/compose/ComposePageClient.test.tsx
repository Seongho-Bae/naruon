/* @vitest-environment jsdom */
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';

const apiClientMock = vi.hoisted(() => ({
  get: vi.fn(async (endpoint: string) => {
    if (endpoint === '/api/mailbox-accounts') {
      return {
        items: [
          {
            id: 1,
            email_address: 'alpha@example.com',
            display_name: 'Alpha',
            is_default_reply: true,
            is_active: true,
          },
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
    if (endpoint === '/api/emails/7') {
      return {
        id: 7,
        mailbox_account_id: 2,
        message_id: '<q2@example.com>',
        thread_id: 'thread-q2',
        sender: '김지현 PM',
        reply_to: 'jihyun@naruon.ai',
        recipients: 'user@naruon.ai',
        subject: 'Q2 출시 계획 및 우선순위 조정',
        date: '2026-05-11T09:30:00Z',
        body: '본문',
      };
    }
    throw new Error(`Unexpected GET ${endpoint}`);
  }),
  post: vi.fn(async () => ({ simulated: true })),
}));

vi.mock('@/lib/api-client', () => ({ apiClient: apiClientMock }));

import { ComposePageClient } from './ComposePageClient';

async function flushAsyncWork() {
  for (let index = 0; index < 5; index += 1) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

async function updateInputValue(element: HTMLInputElement | HTMLTextAreaElement, value: string) {
  const prototype = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value');
  await act(async () => {
    descriptor?.set?.call(element, value);
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  });
}

describe('ComposePageClient', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    root?.unmount();
    root = null;
    container?.remove();
    container = null;
    vi.clearAllMocks();
  });

  it('loads linked mailbox accounts and sends with the selected mailbox account id', async () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<ComposePageClient emailId="7" />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain('회신 계정');
    expect(container.textContent).toContain('Alpha');

    const select = container.querySelector('select');
    expect(select?.value).toBe('2');

    await act(async () => {
      select!.value = '2';
      select!.dispatchEvent(new Event('change', { bubbles: true }));
    });

    await updateInputValue(container.querySelector('input[aria-label="받는 사람"]') as HTMLInputElement, 'beta@example.com');
    await updateInputValue(container.querySelector('input[aria-label="메일 제목"]') as HTMLInputElement, 'Re: Edited subject');
    await updateInputValue(container.querySelector('textarea[aria-label="메일 본문"]') as HTMLTextAreaElement, '답장 본문');
    await flushAsyncWork();

    const sendButton = Array.from(container.querySelectorAll('button')).find((button) => button.textContent?.includes('메일 보내기'));
    await act(async () => {
      sendButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    expect(apiClientMock.post).toHaveBeenCalledWith('/api/emails/send', expect.objectContaining({ mailbox_account_id: 2 }));
  });
});
