/* @vitest-environment jsdom */
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('lucide-react', () => ({
  Activity: () => <svg aria-hidden="true" />,
  Bot: () => <svg aria-hidden="true" />,
  CheckCircle2: () => <svg aria-hidden="true" />,
  FileCode2: () => <svg aria-hidden="true" />,
  GitBranch: () => <svg aria-hidden="true" />,
  RefreshCw: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
  Sparkles: () => <svg aria-hidden="true" />,
}));

import AIHubPage from './page';

const forbiddenIdentityHeaders = [
  'x-user-id',
  'x-organization-id',
  'x-group-id',
  'x-group-ids',
  'x-user-role',
  'x-dev-auth-token',
];

const aiHubSurface = {
  summary_cards: [
    {
      summary_key: 'prompt_templates',
      label_text: '프롬프트',
      value_text: '2',
      detail_text: 'source-backed templates',
      state_code: 'ready',
    },
    {
      summary_key: 'ai_providers',
      label_text: 'AI 에이전트',
      value_text: '1/1',
      detail_text: 'active organization providers',
      state_code: 'ready',
    },
  ],
  prompt_cards: [
    {
      prompt_key: 'prompt_safe',
      prompt_title: '의사결정 로그 요약',
      description_text: '메일에서 판단 포인트를 추출합니다.',
      shared_scope: false,
      owner_label: 'alice',
      updated_at: '2026-05-29T09:30:00Z',
    },
  ],
  workflow_cards: [
    {
      workflow_key: 'workflow_prompt_safe',
      workflow_title: '의사결정 로그 요약 실행 흐름',
      trigger_source: 'prompt_template',
      state_code: 'ready',
      evidence_text: 'active organization provider is available',
    },
  ],
  agent_cards: [
    {
      agent_key: 'agent_primary',
      agent_title: 'Primary OpenAI',
      model_label: 'openai',
      state_code: 'active',
      configured: true,
      governance_text: 'organization llm provider registry',
    },
  ],
  evaluation_metrics: [
    {
      metric_key: 'provider_readiness',
      metric_label: 'Provider 준비도',
      score_value: 100,
      trend_text: '1/1 active providers',
    },
  ],
  run_events: [
    {
      event_key: 'event_provider',
      event_title: 'llm_provider update',
      state_code: 'recorded',
      evidence_source: 'api.llm_providers',
      observed_at: '2026-05-29T09:30:00Z',
      detail_text: 'Updated provider configuration',
    },
  ],
};

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

function clickButton(container: HTMLElement, label: string) {
  const button = Array.from(container.querySelectorAll('button')).find((node) =>
    node.textContent?.includes(label),
  );
  expect(button).not.toBeUndefined();
  act(() => {
    button?.click();
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
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it('fetches the signed AI Hub surface and renders every operational tab', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(aiHubSurface));
    vi.stubGlobal('fetch', fetchMock);
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<AIHubPage />);
    });
    await flushAsyncWork();

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/ai-hub/surface',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      }),
    );
    const firstFetchCall = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const sentHeaders = firstFetchCall[1]?.headers;
    const headerNames =
      sentHeaders && !Array.isArray(sentHeaders) && !(sentHeaders instanceof Headers)
        ? Object.keys(sentHeaders)
        : [];
    const lowerHeaderNames = new Set(headerNames.map((name) => name.toLowerCase()));
    for (const headerName of forbiddenIdentityHeaders) {
      expect(lowerHeaderNames.has(headerName)).toBe(false);
    }
    expect(container.textContent).toContain('AI 허브');
    expect(container.textContent).toContain('의사결정 로그 요약');

    clickButton(container, '워크플로우');
    expect(container.textContent).toContain('의사결정 로그 요약 실행 흐름');

    clickButton(container, 'AI 에이전트');
    expect(container.textContent).toContain('Primary OpenAI');

    clickButton(container, '평가');
    expect(container.textContent).toContain('Provider 준비도');
    expect(container.textContent).toContain('1/1 active providers');

    clickButton(container, '실행 이력');
    expect(container.textContent).toContain('api.llm_providers');
  });

  it('renders a loading state while the AI Hub surface is pending', async () => {
    let resolveFetch: (response: Response) => void = () => {};
    vi.stubGlobal(
      'fetch',
      vi.fn(
        () =>
          new Promise<Response>((resolve) => {
            resolveFetch = resolve;
          }),
      ),
    );
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<AIHubPage />);
    });

    expect(container.textContent).toContain('AI Hub source evidence를 불러오는 중입니다.');

    await act(async () => {
      resolveFetch(jsonResponse(aiHubSurface));
    });
    await flushAsyncWork();
  });

  it('renders a retryable error state when the source surface fails', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ message: 'Internal Server Error' }, false)));
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<AIHubPage />);
    });
    await flushAsyncWork();

    expect(container.querySelector('[role="alert"]')?.textContent).toContain(
      'AI Hub source evidence를 불러오지 못했습니다.',
    );
    expect(container.textContent).toContain('다시 시도');
    expect(consoleError).toHaveBeenCalled();
  });
});
