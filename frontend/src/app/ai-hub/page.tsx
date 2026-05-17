'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { ArrowRight, BookOpen, CheckCircle2, Network, RefreshCw, Sparkles } from 'lucide-react';
import Link from 'next/link';

import { apiClient } from '@/lib/api-client';

type PromptSummary = { id: number; title: string; description?: string };
type HubStatus = 'loading' | 'success' | 'empty' | 'error';

type HubSection = {
  id: string;
  title: string;
  description: string;
  empty: string;
  actionLabel: string;
  actionHref: string;
  icon: React.ElementType;
};

const hubSections: HubSection[] = [
  {
    id: 'context',
    title: '맥락 종합',
    description: '메일, 일정, 사람, 첨부 흐름을 하나의 작업 맥락으로 묶습니다.',
    empty: '아직 연결된 맥락이 없습니다. 받은편지함에서 메일을 선택하면 관련 흐름을 모읍니다.',
    actionLabel: '받은편지함 열기',
    actionHref: '/',
    icon: Network,
  },
  {
    id: 'decisions',
    title: '판단 포인트',
    description: '마감, 리스크, 의사결정 후보를 실행 전에 확인합니다.',
    empty: '검토할 판단 포인트가 없습니다. 새 메일을 동기화하거나 검색을 실행하세요.',
    actionLabel: '맥락 검색',
    actionHref: '/#mobile-search',
    icon: Sparkles,
  },
  {
    id: 'actions',
    title: '실행 항목',
    description: '답장, 일정 연결, 할 일을 다음 행동으로 전환합니다.',
    empty: '실행 항목이 없습니다. 메일 상세에서 할 일 만들기를 실행하세요.',
    actionLabel: '프롬프트 관리',
    actionHref: '/prompt-studio',
    icon: CheckCircle2,
  },
];

function promptDescription(prompt: PromptSummary) {
  return prompt.description?.trim() || '설명을 추가하면 실행 기준과 사용 맥락을 더 빠르게 고를 수 있습니다.';
}

function HubCard({ section, prompt }: { section: HubSection; prompt?: PromptSummary }) {
  const Icon = section.icon;
  const hasPrompt = Boolean(prompt);

  return (
    <section id={section.id} aria-label={section.title} className="scroll-mt-24 flex min-h-64 flex-col rounded-3xl border border-border bg-card/90 p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-primary/10 text-primary">
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h2 className="text-lg font-black text-foreground">{section.title}</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{section.description}</p>
        </div>
      </div>

      <div className="mt-5 flex-1 rounded-2xl border border-border bg-background/70 p-4">
        {hasPrompt ? (
          <article>
            <p className="flex items-center gap-2 text-sm font-black text-foreground">
              <BookOpen className="size-4 text-primary" aria-hidden="true" />
              {prompt?.title}
            </p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{prompt ? promptDescription(prompt) : null}</p>
          </article>
        ) : (
          <div className="space-y-3">
            <p className="text-sm leading-6 text-muted-foreground">{section.empty}</p>
            <Link href={section.actionHref} className="inline-flex min-h-11 items-center gap-2 rounded-2xl border border-border bg-card px-4 text-sm font-bold text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
              {section.actionLabel}
              <ArrowRight className="size-4 text-primary" aria-hidden="true" />
            </Link>
          </div>
        )}
      </div>

      {hasPrompt ? (
        <Link href={section.actionHref} className="mt-4 inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl bg-primary px-4 text-sm font-bold text-primary-foreground shadow-[0_16px_34px_rgba(37,99,255,0.24)] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
          {section.actionLabel}
          <ArrowRight className="size-4" aria-hidden="true" />
        </Link>
      ) : null}
    </section>
  );
}

export default function AIHubPage() {
  const [prompts, setPrompts] = useState<PromptSummary[]>([]);
  const [status, setStatus] = useState<HubStatus>('loading');

  const loadData = useCallback(async () => {
    try {
      const data = await apiClient.get<PromptSummary[]>('/api/prompts');
      setPrompts(data);
      setStatus(data.length > 0 ? 'success' : 'empty');
    } catch {
      setPrompts([]);
      setStatus('error');
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(loadData);
  }, [loadData]);

  const retryLoadData = () => {
    setStatus('loading');
    void loadData();
  };

  return (
    <section className="mx-auto flex min-h-full max-w-7xl flex-col gap-6 p-4 sm:p-6 lg:p-8">
      <header className="rounded-3xl border border-primary/15 bg-gradient-to-br from-primary/8 via-card to-emerald-500/8 p-5 shadow-sm sm:p-6">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">Naruon Workspace</p>
        <h1 className="mt-3 text-3xl font-black tracking-tight text-foreground">AI 허브</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
          메일, 일정, 관계를 맥락·판단·실행으로 정리합니다.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/" className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-primary px-4 text-sm font-bold text-primary-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
            받은편지함에서 메일 선택하기
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
          <Link href="/prompt-studio" className="inline-flex min-h-11 items-center gap-2 rounded-2xl border border-border bg-card px-4 text-sm font-bold text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
            프롬프트 관리
          </Link>
        </div>
      </header>

      {status === 'loading' ? (
        <div role="status" aria-live="polite" className="rounded-3xl border border-border bg-card p-6 text-sm font-bold text-muted-foreground shadow-sm">
          AI 허브를 불러오는 중입니다.
        </div>
      ) : null}

      {status === 'error' ? (
        <div role="alert" className="rounded-3xl border border-destructive/30 bg-destructive/10 p-6 text-sm font-bold text-destructive shadow-sm">
          AI 허브 데이터를 불러오지 못했습니다.
          <button type="button" onClick={retryLoadData} className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-2xl border border-destructive/30 bg-card px-4 text-sm font-bold text-destructive focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
            <RefreshCw className="size-4" aria-hidden="true" />
            다시 시도
          </button>
        </div>
      ) : null}

      {status !== 'loading' && status !== 'error' ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {hubSections.map((section, index) => (
            <HubCard key={section.title} section={section} prompt={prompts[index]} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
