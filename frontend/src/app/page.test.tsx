/* @vitest-environment jsdom */
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/components/EmailList', () => ({
  EmailList: ({ onSelectEmail }: { onSelectEmail: (id: number, email?: { id: number; subject: string; snippet: string; unread?: boolean; reply_count?: number }) => void }) => (
    <div>
      <button onClick={() => onSelectEmail(1, { id: 1, subject: '출시 일정 검토 요청', snippet: '우선순위 조정', unread: true, reply_count: 3 })}>Inbox mock</button>
      <button onClick={() => onSelectEmail(99, { id: 99, subject: '선택된 별도 메일', snippet: 'summary subset 밖에 있는 메일', unread: false, reply_count: 1 })}>Out-of-summary mock</button>
    </div>
  ),
}));

vi.mock('@/components/EmailDetail', () => ({
  EmailDetail: ({ emailId }: { emailId: number | null }) => <div>Detail mock {emailId}</div>,
}));

vi.mock('@/components/ui/resizable', () => ({
  ResizablePanelGroup: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ResizablePanel: ({ children }: { children: React.ReactNode }) => <section>{children}</section>,
  ResizableHandle: () => <div />,
}));

vi.mock('next/dynamic', () => ({
  default: () => () => <div>Graph mock</div>,
}));

const apiClientMock = vi.hoisted(() => ({
  getBearerToken: vi.fn(() => null),
  getCurrentUserId: vi.fn(() => 'testuser'),
  getCurrentOrganizationId: vi.fn(() => 'org-local-dev'),
  get: vi.fn(async () => ({
    emails: [
      { id: 1, subject: '출시 일정 검토 요청', snippet: '우선순위 조정', unread: true, reply_count: 3 },
      { id: 2, subject: '회의 일정 확인', snippet: '참석자 확인', unread: false, reply_count: 1 },
    ],
  })),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: apiClientMock,
}));

import Home from './page';

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

describe('Home dashboard', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  beforeEach(() => {
    vi.stubGlobal('window', window);
    window.matchMedia = vi.fn().mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }) as unknown as typeof window.matchMedia;
  });

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    vi.clearAllMocks();
  });

  it('renders board-style summary cards and a judgment/action execution rail', async () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<Home />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain('오늘의 판단 포인트');
    expect(container.textContent).toContain('일정 연결');
    expect(container.textContent).toContain('대기 중 작업');
    expect(container.textContent).toContain('빠른 실행');
    expect(container.textContent).toContain('맥락 종합');
    expect(container.textContent).toContain('판단 포인트');
    expect(container.textContent).toContain('실행 항목');

    const actionLinks = Array.from(container.querySelectorAll('a')).map((link) => ({
      text: link.textContent?.trim(),
      href: link.getAttribute('href'),
    }));
    expect(actionLinks).toEqual(expect.arrayContaining([
      expect.objectContaining({ text: expect.stringContaining('할 일 만들기'), href: '/ai-hub/actions' }),
      expect.objectContaining({ text: expect.stringContaining('캘린더 반영'), href: '/ai-hub/actions#calendar-bridge' }),
      expect.objectContaining({ text: expect.stringContaining('답장 초안'), href: '/compose' }),
    ]));
  });

  it('uses the actually selected inbox email for the right rail even when it is outside the summary subset', async () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<Home />);
    });
    await flushAsyncWork();

    const outOfSummaryButton = Array.from(container.querySelectorAll('button')).find((button) => button.textContent === 'Out-of-summary mock');
    await act(async () => {
      outOfSummaryButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    expect(container.textContent).toContain('선택된 별도 메일');
    expect(container.textContent).toContain('summary subset 밖에 있는 메일');
  });
});
