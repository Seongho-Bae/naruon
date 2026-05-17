/* @vitest-environment jsdom */
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('lucide-react', () => ({
  AlertCircle: () => <svg aria-hidden="true" />,
  ArrowRight: () => <svg aria-hidden="true" />,
  BookOpen: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  Network: () => <svg aria-hidden="true" />,
  RefreshCw: () => <svg aria-hidden="true" />,
  Sparkles: () => <svg aria-hidden="true" />,
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
    expect(container.textContent).toContain('맥락 종합');
    expect(container.textContent).toContain('판단 포인트');
    expect(container.textContent).toContain('실행 항목');
    expect(container.textContent).toContain('Q2 출시 판단');
    expect(container.querySelector('section#context[aria-label="맥락 종합"]')).not.toBeNull();
    expect(container.querySelector('section#decisions[aria-label="판단 포인트"]')).not.toBeNull();
    expect(container.querySelector('section#actions[aria-label="실행 항목"]')).not.toBeNull();
    expect(container.textContent).not.toContain('최근 AI 요약');
    expect(container.textContent).not.toContain('AI Hub');
    expect(container.textContent).not.toContain('설명 없음');
  });

  it('renders an accessible loading state while the AI hub loads', async () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)));
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<AIHubPage />);
    });

    expect(container.querySelector('[role="status"]')?.textContent).toContain('AI 허브를 불러오는 중입니다.');
  });

  it('renders an accessible error state with retry', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ detail: 'failed' }, false)));
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<AIHubPage />);
    });
    await flushAsyncWork();

    expect(container.querySelector('[role="alert"]')?.textContent).toContain('AI 허브 데이터를 불러오지 못했습니다.');
    expect(Array.from(container.querySelectorAll('button')).some((button) => button.textContent?.includes('다시 시도'))).toBe(true);
  });
});
