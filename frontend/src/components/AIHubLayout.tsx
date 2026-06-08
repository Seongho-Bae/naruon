"use client";

import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Bot,
  FileCode2,
  GitBranch,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

import { apiClient } from '@/lib/api-client';

type SurfaceStatus = 'loading' | 'ready' | 'error';
type TabId = 'prompts' | 'workflows' | 'agents' | 'evaluation' | 'runs';

type SummaryCard = {
  summary_key: string;
  label_text: string;
  value_text: string;
  detail_text: string;
  state_code: string;
};

type PromptCard = {
  prompt_key: string;
  prompt_title: string;
  description_text: string | null;
  shared_scope: boolean;
  owner_label: string;
  updated_at: string | null;
};

type WorkflowCard = {
  workflow_key: string;
  workflow_title: string;
  trigger_source: string;
  state_code: string;
  evidence_text: string;
};

type AgentCard = {
  agent_key: string;
  agent_title: string;
  model_label: string;
  state_code: string;
  configured: boolean;
  governance_text: string;
};

type EvaluationMetric = {
  metric_key: string;
  metric_label: string;
  score_value: number;
  trend_text: string;
};

type RunEvent = {
  event_key: string;
  event_title: string;
  state_code: string;
  evidence_source: string;
  observed_at: string | null;
  detail_text: string | null;
};

type AiHubSurfaceResponse = {
  summary_cards: SummaryCard[];
  prompt_cards: PromptCard[];
  workflow_cards: WorkflowCard[];
  agent_cards: AgentCard[];
  evaluation_metrics: EvaluationMetric[];
  run_events: RunEvent[];
};

const tabs = [
  { id: 'prompts', label: '프롬프트 스튜디오', icon: FileCode2 },
  { id: 'workflows', label: '워크플로우', icon: GitBranch },
  { id: 'agents', label: 'AI 에이전트', icon: Bot },
  { id: 'evaluation', label: '평가', icon: ShieldCheck },
  { id: 'runs', label: '실행 이력', icon: Activity },
] as const;

function getSafeErrorSummary(error: unknown) {
  if (error instanceof Error) return error.message;
  return 'unknown error';
}

function formatDateTime(value: string | null) {
  if (!value) return '기록 없음';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '기록 없음';
  return new Intl.DateTimeFormat('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed);
}

function stateLabel(stateCode: string) {
  const labels: Record<string, string> = {
    active: '활성',
    attention: '점검',
    configured: '구성됨',
    empty: '없음',
    needs_key: '키 필요',
    needs_provider: 'Provider 필요',
    ready: '준비됨',
    recorded: '기록됨',
  };
  return labels[stateCode] ?? stateCode;
}

function stateClassName(stateCode: string) {
  if (stateCode === 'active' || stateCode === 'ready' || stateCode === 'recorded') {
    return 'border-green-200 bg-green-50 text-green-700';
  }
  if (stateCode === 'attention' || stateCode.startsWith('needs_')) {
    return 'border-amber-200 bg-amber-50 text-amber-700';
  }
  return 'border-border bg-secondary text-muted-foreground';
}

function StatusBadge({ stateCode }: { stateCode: string }) {
  return (
    <span className={`inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-[11px] font-bold ${stateClassName(stateCode)}`}>
      {stateLabel(stateCode)}
    </span>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-card p-8 text-center">
      <p className="font-bold text-foreground">{title}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{detail}</p>
    </div>
  );
}

function SummaryGrid({ cards }: { cards: SummaryCard[] }) {
  return (
    <section aria-label="AI Hub source-backed summary" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => (
        <article key={card.summary_key} className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm font-bold text-muted-foreground">{card.label_text}</p>
            <StatusBadge stateCode={card.state_code} />
          </div>
          <p className="mt-4 text-3xl font-black text-foreground">{card.value_text}</p>
          <p className="mt-1 text-xs font-semibold text-muted-foreground">{card.detail_text}</p>
        </article>
      ))}
    </section>
  );
}

function PromptPanel({ prompts }: { prompts: PromptCard[] }) {
  if (prompts.length === 0) {
    return <EmptyState title="등록된 프롬프트가 없습니다." detail="프롬프트 스튜디오에서 저장된 템플릿이 생기면 이 화면에 연결됩니다." />;
  }
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {prompts.map((prompt) => (
        <article key={prompt.prompt_key} className="rounded-lg border border-border bg-card p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="truncate text-base font-black">{prompt.prompt_title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{prompt.description_text ?? '설명 없음'}</p>
            </div>
            <StatusBadge stateCode={prompt.shared_scope ? 'ready' : 'configured'} />
          </div>
          <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="font-bold text-muted-foreground">소유자</dt>
              <dd className="mt-1 font-semibold">{prompt.owner_label}</dd>
            </div>
            <div>
              <dt className="font-bold text-muted-foreground">업데이트</dt>
              <dd className="mt-1 font-semibold">{formatDateTime(prompt.updated_at)}</dd>
            </div>
          </dl>
        </article>
      ))}
    </div>
  );
}

function WorkflowPanel({ workflows }: { workflows: WorkflowCard[] }) {
  if (workflows.length === 0) {
    return <EmptyState title="실행 흐름으로 만들 프롬프트가 없습니다." detail="저장된 프롬프트와 활성 Provider가 연결되면 실행 후보가 생성됩니다." />;
  }
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {workflows.map((workflow) => (
        <article key={workflow.workflow_key} className="rounded-lg border border-border bg-card p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <h2 className="text-base font-black">{workflow.workflow_title}</h2>
            <StatusBadge stateCode={workflow.state_code} />
          </div>
          <p className="mt-4 text-sm font-bold text-primary">{workflow.trigger_source}</p>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{workflow.evidence_text}</p>
        </article>
      ))}
    </div>
  );
}

function AgentsPanel({ agents }: { agents: AgentCard[] }) {
  if (agents.length === 0) {
    return <EmptyState title="조직 Provider가 없습니다." detail="설정의 LLM Provider registry가 구성되면 AI 에이전트 실행 후보로 표시됩니다." />;
  }
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {agents.map((agent) => (
        <article key={agent.agent_key} className="rounded-lg border border-border bg-card p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <h2 className="text-base font-black">{agent.agent_title}</h2>
            <StatusBadge stateCode={agent.state_code} />
          </div>
          <dl className="mt-5 space-y-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <dt className="font-bold text-muted-foreground">Provider</dt>
              <dd className="font-semibold">{agent.model_label}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt className="font-bold text-muted-foreground">Credential</dt>
              <dd className="font-semibold">{agent.configured ? 'configured' : 'missing'}</dd>
            </div>
          </dl>
          <p className="mt-4 text-xs leading-5 text-muted-foreground">{agent.governance_text}</p>
        </article>
      ))}
    </div>
  );
}

function EvaluationPanel({ metrics }: { metrics: EvaluationMetric[] }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {metrics.map((metric) => (
        <article key={metric.metric_key} className="rounded-lg border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-base font-black">{metric.metric_label}</h2>
            <span className="text-2xl font-black text-primary">{metric.score_value}</span>
          </div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-secondary">
            <div className="h-full rounded-full bg-primary" style={{ width: `${Math.max(0, Math.min(metric.score_value, 100))}%` }} />
          </div>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">{metric.trend_text}</p>
        </article>
      ))}
    </div>
  );
}

function RunHistoryPanel({ events }: { events: RunEvent[] }) {
  if (events.length === 0) {
    return <EmptyState title="기록된 실행 증거가 없습니다." detail="프롬프트 변경 또는 Provider 감사 이벤트가 생기면 실행 이력으로 정렬됩니다." />;
  }
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
      <div className="grid grid-cols-[minmax(0,1fr)_9rem_8rem] gap-4 border-b border-border px-4 py-3 text-xs font-black text-muted-foreground max-md:hidden">
        <span>이벤트</span>
        <span>증거</span>
        <span>시간</span>
      </div>
      <div className="divide-y divide-border">
        {events.map((event) => (
          <article key={event.event_key} className="grid gap-3 px-4 py-4 md:grid-cols-[minmax(0,1fr)_9rem_8rem] md:items-center">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-black">{event.event_title}</h2>
                <StatusBadge stateCode={event.state_code} />
              </div>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">{event.detail_text ?? '상세 증거 없음'}</p>
            </div>
            <p className="text-sm font-semibold text-primary">{event.evidence_source}</p>
            <p className="text-sm font-semibold text-muted-foreground">{formatDateTime(event.observed_at)}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

export function AIHubLayout() {
  const [activeTab, setActiveTab] = useState<TabId>('prompts');
  const [surfaceStatus, setSurfaceStatus] = useState<SurfaceStatus>('loading');
  const [surface, setSurface] = useState<AiHubSurfaceResponse | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [refreshNonce, setRefreshNonce] = useState(0);

  const requestRefresh = () => {
    setSurfaceStatus('loading');
    setErrorText(null);
    setRefreshNonce((value) => value + 1);
  };

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<AiHubSurfaceResponse>('/api/ai-hub/surface')
      .then((data) => {
        if (cancelled) return;
        setSurface(data);
        setSurfaceStatus('ready');
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        console.error('AI Hub surface fetch error', getSafeErrorSummary(error));
        setSurface(null);
        setErrorText('AI Hub source evidence를 불러오지 못했습니다.');
        setSurfaceStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, [refreshNonce]);

  const activeTabLabel = useMemo(
    () => tabs.find((tab) => tab.id === activeTab)?.label ?? 'AI 허브',
    [activeTab],
  );

  return (
    <div className="flex h-full min-h-0 flex-col bg-background text-foreground">
      <header className="shrink-0 border-b border-border bg-card px-4 py-4 md:px-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="flex items-center gap-3 text-xl font-black md:text-2xl">
            <Sparkles className="size-6 text-primary" aria-hidden="true" />
            AI 허브
          </h1>
          <button
            type="button"
            onClick={requestRefresh}
            className="inline-flex h-10 items-center gap-2 rounded-lg border border-border bg-background px-3 text-sm font-bold hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
          >
            <RefreshCw className="size-4" aria-hidden="true" />
            새로고침
          </button>
        </div>
        <nav aria-label="AI 허브 섹션" className="mt-4 flex gap-2 overflow-x-auto pb-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex h-10 shrink-0 items-center gap-2 rounded-lg px-3 text-sm font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 ${
                activeTab === tab.id
                  ? 'bg-primary text-primary-foreground'
                  : 'border border-border bg-background text-muted-foreground hover:bg-secondary'
              }`}
            >
              <tab.icon className="size-4" aria-hidden="true" />
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden bg-background p-4 pb-[calc(6rem+env(safe-area-inset-bottom))] md:p-8">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
          {surfaceStatus === 'loading' && (
            <div role="status" className="rounded-lg border border-border bg-card p-6 font-bold text-primary">
              AI Hub source evidence를 불러오는 중입니다.
            </div>
          )}

          {surfaceStatus === 'error' && (
            <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
              <p className="font-black">{errorText}</p>
              <button
                type="button"
                onClick={requestRefresh}
                className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                다시 시도
              </button>
            </div>
          )}

          {surfaceStatus === 'ready' && surface && (
            <>
              <SummaryGrid cards={surface.summary_cards} />
              <section aria-label={activeTabLabel} className="min-h-[24rem]">
                {activeTab === 'prompts' && <PromptPanel prompts={surface.prompt_cards} />}
                {activeTab === 'workflows' && <WorkflowPanel workflows={surface.workflow_cards} />}
                {activeTab === 'agents' && <AgentsPanel agents={surface.agent_cards} />}
                {activeTab === 'evaluation' && <EvaluationPanel metrics={surface.evaluation_metrics} />}
                {activeTab === 'runs' && <RunHistoryPanel events={surface.run_events} />}
              </section>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
