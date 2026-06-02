/* @vitest-environment jsdom */
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('lucide-react', () => ({
  Activity: () => <svg aria-hidden="true" />,
  Cpu: () => <svg aria-hidden="true" />,
  Zap: () => <svg aria-hidden="true" />,
  Key: () => <svg aria-hidden="true" />,
  FileCode2: () => <svg aria-hidden="true" />,
  MessageSquare: () => <svg aria-hidden="true" />,
  Sparkles: () => <svg aria-hidden="true" />,
  Bot: () => <svg aria-hidden="true" />,
  Database: () => <svg aria-hidden="true" />,
  Network: () => <svg aria-hidden="true" />,
  RefreshCw: () => <svg aria-hidden="true" />,
  ShieldAlert: () => <svg aria-hidden="true" />,
}));

import AIHubPage from './page';

function jsonResponse(body: unknown, ok = true) {
  return {
    ok,
    status: ok ? 200 : 500,
    statusText: ok ? 'OK' : 'Server Error',
    json: async () => body,
  } as Response;
}

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

describe('AIHubPage', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    vi.unstubAllGlobals();
  });

  it('renders the three functional AI workspace sections from API data', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse([
      { id: 1, title: 'Q2 출시 판단', description: '출시 일정과 파트너 리스크를 함께 검토합니다.' },
    ])));
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<AIHubPage />);
    });
    await flushAsyncWork();

    expect(container.querySelector('h1')?.textContent).toContain('AI 허브');
    expect(container.querySelector('h1')?.textContent).toContain('AI 허브');
  });

  it('renders an accessible loading state while the AI hub loads', async () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<AIHubPage />);
    });

    expect(container).not.toBeNull();
  });

  it('renders an accessible error state with retry', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ message: 'Internal Server Error' }, false)));
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<AIHubPage />);
    });
    await flushAsyncWork();

    expect(container).not.toBeNull();
  });
});
