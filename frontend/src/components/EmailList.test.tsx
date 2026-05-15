/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { EmailList } from "./EmailList";
import { apiClient } from "@/lib/api-client";

function jsonResponse(body: unknown) {
  return {
    ok: true,
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

async function flushAsyncWork() {
  for (let index = 0; index < 5; index += 1) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

async function updateInputValue(element: HTMLInputElement, value: string) {
  const descriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
  await act(async () => {
    descriptor?.set?.call(element, value);
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  });
}

describe("EmailList", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  beforeEach(() => {
    apiClient.setBaseUrl('');
    apiClient.setDevHeaderAuthEnabled(true);
  });

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    vi.unstubAllGlobals();
  });

  it("renders the branded dense inbox and selected thread state", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/mailbox-accounts') {
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                id: 1,
                email_address: 'alpha@example.com',
                display_name: 'Alpha',
                is_default_reply: true,
                is_active: true,
              },
            ],
          }),
        );
      }
      if (url === '/api/emails') {
        return Promise.resolve(
          jsonResponse({
            emails: [
              {
                id: 7,
                mailbox_account_id: 1,
                sender: "김지현 PM",
                subject: null,
                date: "2026-05-11T09:30:00Z",
                snippet: "Q2 출시 계획과 우선순위 조정 요청입니다.",
                unread: true,
                reply_count: 3,
              },
            ],
          }),
        );
      }
      throw new Error(`Unexpected GET ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailList onSelectEmail={vi.fn()} selectedEmailId={7} />);
    });
    await flushAsyncWork();

    const selectedThread = container.querySelector('button[aria-current="true"]');

    expect(fetchMock).toHaveBeenCalledWith("/api/emails", expect.any(Object));
    expect(container.textContent).toContain("받은편지함");
    expect(container.textContent).toContain("맥락 종합");
    expect(container.textContent).toContain("실행 항목");
    expect(container.textContent).toContain("(제목 없음)");
    expect(container.textContent).toContain("새 메일");
    expect(container.textContent).toContain("3개 메시지");
    expect(container.textContent).toContain('Alpha');
    expect(selectedThread).not.toBeNull();
    expect(selectedThread?.className).toContain("min-h-20");
  });

  it("queues an email when the row is swiped right", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/mailbox-accounts') {
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                id: 1,
                email_address: 'alpha@example.com',
                display_name: 'Alpha',
                is_default_reply: true,
                is_active: true,
              },
            ],
          }),
        );
      }
      if (url === '/api/emails') {
        return Promise.resolve(
          jsonResponse({
            emails: [
              {
                id: 7,
                mailbox_account_id: 1,
                sender: "김지현 PM",
                subject: "출시 일정 검토 요청",
                date: "2026-05-11T09:30:00Z",
                snippet: "Q2 출시 계획과 우선순위 조정 요청입니다.",
                unread: true,
                reply_count: 3,
              },
            ],
          }),
        );
      }
      if (url === '/api/execution-items/from-email' && init?.method === 'POST') {
        return Promise.resolve(
          jsonResponse({
            item: {
              id: 70,
              user_id: 'testuser',
              source_email_id: 7,
              source_thread_id: 'thread-q2',
              source_message_id: '<q2@example.com>',
              title: '출시 일정 검토 요청',
              sender: '김지현 PM',
              status: 'queued',
              created_at: '2026-05-14T00:00:00.000Z',
              updated_at: '2026-05-14T00:00:00.000Z',
              completed_at: null,
            },
          }),
        );
      }
      throw new Error(`Unexpected ${init?.method || 'GET'} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailList onSelectEmail={vi.fn()} selectedEmailId={null} />);
    });
    await flushAsyncWork();

    const row = container.querySelector('button[aria-label*="오른쪽으로 밀면 실행 목록"]');
    expect(row).not.toBeNull();
    const setPointerCapture = vi.fn();
    const releasePointerCapture = vi.fn();
    Object.assign(row as HTMLButtonElement, { setPointerCapture, releasePointerCapture });

    await act(async () => {
      row?.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, pointerId: 1, clientX: 10, clientY: 10 }));
    });
    expect(setPointerCapture).not.toHaveBeenCalled();

    await act(async () => {
      row?.dispatchEvent(new PointerEvent("pointermove", { bubbles: true, pointerId: 1, clientX: 130, clientY: 10 }));
      row?.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, pointerId: 1, clientX: 130, clientY: 10 }));
    });

    expect(setPointerCapture).toHaveBeenCalledWith(1);
    expect(releasePointerCapture).toHaveBeenCalledWith(1);
    expect(window.localStorage.getItem("naruon.executionQueue.org-local-dev.testuser") || "").toContain("출시 일정 검토 요청");
    expect(container.textContent).toContain("실행 목록에 담았습니다");
  });

  it("offers visible tap fallback buttons for queueing and completing execution items", async () => {
    window.localStorage.setItem(
      "naruon.executionQueue.org-local-dev.testuser",
      JSON.stringify([
        {
          id: 70,
          sourceMailboxAccountId: 1,
          sourceEmailId: 7,
          sourceThreadId: "thread-q2",
          sourceMessageId: "<q2@example.com>",
          sourceSnippet: "Q2 출시 계획과 우선순위 조정 요청입니다.",
          title: "출시 일정 검토 요청",
          sender: "김지현 PM",
          status: "queued",
          createdAt: "2026-05-14T00:00:00.000Z",
          updatedAt: "2026-05-14T00:00:00.000Z",
          completedAt: null,
        },
      ]),
    );
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/mailbox-accounts') {
        return Promise.resolve(jsonResponse({ items: [] }));
      }
      if (url === '/api/emails') {
        return Promise.resolve(
          jsonResponse({
            emails: [
              {
                id: 7,
                mailbox_account_id: 1,
                sender: "김지현 PM",
                subject: "출시 일정 검토 요청",
                date: "2026-05-11T09:30:00Z",
                snippet: "Q2 출시 계획과 우선순위 조정 요청입니다.",
                unread: true,
                reply_count: 3,
              },
            ],
          }),
        );
      }
      if (url === '/api/execution-items/from-email' && init?.method === 'POST') {
        return Promise.resolve(
          jsonResponse({
            item: {
              id: 70,
              user_id: 'testuser',
              source_mailbox_account_id: 1,
              source_email_id: 7,
              source_thread_id: 'thread-q2',
              source_message_id: '<q2@example.com>',
              source_snippet: 'Q2 출시 계획과 우선순위 조정 요청입니다.',
              title: '출시 일정 검토 요청',
              sender: '김지현 PM',
              status: 'queued',
              created_at: '2026-05-14T00:00:00.000Z',
              updated_at: '2026-05-14T00:00:00.000Z',
              completed_at: null,
            },
          }),
        );
      }
      if (url === '/api/execution-items/70' && init?.method === 'PATCH') {
        return Promise.resolve(
          jsonResponse({
            item: {
              id: 70,
              user_id: 'testuser',
              source_mailbox_account_id: 1,
              source_email_id: 7,
              source_thread_id: 'thread-q2',
              source_message_id: '<q2@example.com>',
              source_snippet: 'Q2 출시 계획과 우선순위 조정 요청입니다.',
              title: '출시 일정 검토 요청',
              sender: '김지현 PM',
              status: 'done',
              created_at: '2026-05-14T00:00:00.000Z',
              updated_at: '2026-05-14T00:00:00.000Z',
              completed_at: '2026-05-14T00:01:00.000Z',
            },
          }),
        );
      }
      throw new Error(`Unexpected ${init?.method || 'GET'} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailList onSelectEmail={vi.fn()} selectedEmailId={null} />);
    });
    await flushAsyncWork();

    const queueButton = container.querySelector<HTMLButtonElement>('button[aria-label="출시 일정 검토 요청 메일을 실행 목록에 담기"]');
    const doneButton = container.querySelector<HTMLButtonElement>('button[aria-label="출시 일정 검토 요청 실행 항목 완료 처리"]');
    const scrollRoot = container.querySelector<HTMLElement>('[data-slot="scroll-area"]');

    expect(queueButton).not.toBeNull();
    expect(doneButton).not.toBeNull();
    expect(queueButton?.className).not.toContain("sr-only");
    expect(doneButton?.className).not.toContain("sr-only");
    expect(queueButton?.textContent).toContain("실행 목록에 추가");
    expect(scrollRoot?.className).toContain("min-h-0");

    await act(async () => {
      queueButton?.click();
    });
    await flushAsyncWork();
    expect(container.querySelector('[role="status"][aria-live="polite"]')?.textContent).toContain('실행 목록에 담았습니다');
    await act(async () => {
      doneButton?.click();
    });
    await flushAsyncWork();

    expect(fetchMock).toHaveBeenCalledWith('/api/execution-items/from-email', expect.objectContaining({ method: 'POST' }));
    expect(fetchMock).toHaveBeenCalledWith('/api/execution-items/70', expect.objectContaining({ method: 'PATCH' }));
    expect(container.textContent).toContain("완료 처리했습니다");
  });

  it("filters the inbox by mailbox account", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === '/api/mailbox-accounts') {
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: 1, email_address: 'alpha@example.com', display_name: 'Alpha', is_default_reply: true, is_active: true },
              { id: 2, email_address: 'beta@example.com', display_name: 'Beta', is_default_reply: false, is_active: true },
            ],
          }),
        );
      }
      if (url === '/api/emails') {
        return Promise.resolve(jsonResponse({ emails: [] }));
      }
      if (url === '/api/emails?mailbox_account_id=2') {
        return Promise.resolve(jsonResponse({
          emails: [
            {
              id: 9,
              mailbox_account_id: 2,
              sender: 'beta@example.com',
              subject: 'Beta only',
              date: '2026-05-11T09:30:00Z',
              snippet: 'beta 계정 메일',
              unread: false,
              reply_count: 1,
            },
          ],
        }));
      }
      throw new Error(`Unexpected GET ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailList onSelectEmail={vi.fn()} selectedEmailId={null} />);
    });
    await flushAsyncWork();

    const select = container.querySelector('select[aria-label="Mailbox account filter"]') as HTMLSelectElement;
    expect(select).not.toBeNull();

    await act(async () => {
      select.value = '2';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await flushAsyncWork();

    expect(fetchMock).toHaveBeenCalledWith('/api/emails?mailbox_account_id=2', expect.any(Object));
    expect(container.textContent).toContain('Beta only');
  });

  it("keeps mailbox scope when searching", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/mailbox-accounts') {
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: 1, email_address: 'alpha@example.com', display_name: 'Alpha', is_default_reply: true, is_active: true },
              { id: 2, email_address: 'beta@example.com', display_name: 'Beta', is_default_reply: false, is_active: true },
            ],
          }),
        );
      }
      if (url === '/api/emails') {
        return Promise.resolve(jsonResponse({ emails: [] }));
      }
      if (url === '/api/emails?mailbox_account_id=2') {
        return Promise.resolve(jsonResponse({ emails: [] }));
      }
      if (url === '/api/search' && init?.method === 'POST') {
        return Promise.resolve(jsonResponse({
          results: [
            {
              id: 9,
              mailbox_account_id: 2,
              sender: 'beta@example.com',
              subject: 'Beta only',
              date: '2026-05-11T09:30:00Z',
              snippet: 'beta 계정 메일',
              unread: false,
              reply_count: 1,
            },
          ],
        }));
      }
      throw new Error(`Unexpected ${init?.method || 'GET'} ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailList onSelectEmail={vi.fn()} selectedEmailId={null} />);
    });
    await flushAsyncWork();

    const select = container.querySelector('select[aria-label="Mailbox account filter"]') as HTMLSelectElement;
    await act(async () => {
      select.value = '2';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await flushAsyncWork();

    const searchInput = container.querySelector('input[aria-label="Search emails"]') as HTMLInputElement;
    await updateInputValue(searchInput, 'beta');

    const searchForm = container.querySelector('form');
    await act(async () => {
      searchForm?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    });

    expect(fetchMock).toHaveBeenCalledWith('/api/search', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ query: 'beta', mailbox_account_id: 2 }),
    }));
    expect(container.textContent).toContain('Beta');
    expect(container.textContent).toContain('Beta only');
  });

  it("labels legacy restored rows that are included in a mailbox-filtered bridge view", async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/mailbox-accounts') {
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: 2, email_address: 'beta@example.com', display_name: 'Beta', is_default_reply: true, is_active: true },
            ],
          }),
        );
      }
      if (url === '/api/emails') {
        return Promise.resolve(jsonResponse({ emails: [] }));
      }
      if (url === '/api/emails?mailbox_account_id=2') {
        return Promise.resolve(jsonResponse({ emails: [] }));
      }
      if (url === '/api/search' && init?.method === 'POST') {
        return Promise.resolve(jsonResponse({
          results: [
            {
              id: 19,
              mailbox_account_id: null,
              sender: 'legacy@example.com',
              subject: 'Legacy restored thread',
              date: '2026-05-11T09:30:00Z',
              snippet: 'legacy row included in beta mailbox scope',
              unread: false,
              reply_count: 2,
            },
          ],
        }));
      }
      throw new Error(`Unexpected ${init?.method || 'GET'} ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailList onSelectEmail={vi.fn()} selectedEmailId={null} />);
    });
    await flushAsyncWork();

    const select = container.querySelector('select[aria-label="Mailbox account filter"]') as HTMLSelectElement;
    await act(async () => {
      select.value = '2';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await flushAsyncWork();

    const searchInput = container.querySelector('input[aria-label="Search emails"]') as HTMLInputElement;
    await updateInputValue(searchInput, 'legacy');
    const searchForm = container.querySelector('form');
    await act(async () => {
      searchForm?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    });
    await flushAsyncWork();

    expect(container.textContent).toContain('Legacy restored thread');
    expect(container.textContent).toContain('이전 복원 메일');
  });

  it("preserves the selected mailbox scope when opening legacy search results", async () => {
    const onSelectEmail = vi.fn();
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/mailbox-accounts') {
        return Promise.resolve(
          jsonResponse({
            items: [
              { id: 2, email_address: 'beta@example.com', display_name: 'Beta', is_default_reply: true, is_active: true },
            ],
          }),
        );
      }
      if (url === '/api/emails') {
        return Promise.resolve(jsonResponse({ emails: [] }));
      }
      if (url === '/api/emails?mailbox_account_id=2') {
        return Promise.resolve(jsonResponse({ emails: [] }));
      }
      if (url === '/api/search' && init?.method === 'POST') {
        return Promise.resolve(jsonResponse({
          results: [
            {
              id: 19,
              mailbox_account_id: null,
              sender: 'legacy@example.com',
              subject: 'Legacy restored thread',
              date: '2026-05-11T09:30:00Z',
              snippet: 'legacy row included in beta mailbox scope',
              unread: false,
              reply_count: 2,
            },
          ],
        }));
      }
      throw new Error(`Unexpected ${init?.method || 'GET'} ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailList onSelectEmail={onSelectEmail} selectedEmailId={null} />);
    });
    await flushAsyncWork();

    const select = container.querySelector('select[aria-label="Mailbox account filter"]') as HTMLSelectElement;
    await act(async () => {
      select.value = '2';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await flushAsyncWork();

    const searchInput = container.querySelector('input[aria-label="Search emails"]') as HTMLInputElement;
    await updateInputValue(searchInput, 'legacy');

    const searchForm = container.querySelector('form');
    await act(async () => {
      searchForm?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    });
    await flushAsyncWork();

    const legacyResultButton = container.querySelector<HTMLButtonElement>('button[aria-label*="Legacy restored thread"]');
    await act(async () => {
      legacyResultButton?.click();
    });

    expect(onSelectEmail).toHaveBeenCalledWith(
      19,
      expect.objectContaining({ mailbox_account_id: null, subject: 'Legacy restored thread' }),
      2,
    );
  });
});
