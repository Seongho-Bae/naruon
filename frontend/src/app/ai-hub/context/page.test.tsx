/* @vitest-environment jsdom */
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';

const apiClientMock = vi.hoisted(() => ({
  get: vi.fn(async () => ({ emails: [] })),
  post: vi.fn(async () => ({
    results: [
      {
        id: 7,
        subject: 'launch topic',
        snippet: '검색어와 일치하는 출시 맥락입니다.',
        unread: true,
        reply_count: 2,
      },
    ],
  })),
}));

vi.mock('@/lib/api-client', () => ({ apiClient: apiClientMock }));

import AIHubContextPage from './page';

async function flushAsyncWork() {
  for (let index = 0; index < 5; index += 1) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

describe('AIHubContextPage', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    window.history.replaceState({}, '', '/');
    vi.clearAllMocks();
  });

  it('uses the header search query to load filtered context evidence', async () => {
    window.history.pushState({}, '', '/ai-hub/context?q=launch');
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<AIHubContextPage />);
    });
    await flushAsyncWork();

    expect(apiClientMock.get).not.toHaveBeenCalledWith('/api/emails?limit=24');
    expect(apiClientMock.post).toHaveBeenCalledWith('/api/search', { query: 'launch' });
    expect(container.textContent).toContain('검색어: launch');
    expect(container.textContent).toContain('launch topic');
  });
});
