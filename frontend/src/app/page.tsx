"use client";

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

import { apiClient } from '@/lib/api-client';
import { EmailList } from '@/components/EmailList';
import { EmailDetail } from '@/components/EmailDetail';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import dynamic from 'next/dynamic';
import { Badge } from '@/components/ui/badge';
import { CalendarDays, CheckCircle2, Network, PenLine, Target } from 'lucide-react';
import { listExecutionQueue, refreshExecutionQueue, subscribeExecutionQueue, type ExecutionQueueItem } from '@/lib/execution-queue';
import { deriveWorkspaceInsights, type WorkspaceInsightEmail } from '@/lib/workspace-insights';
import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';
const NetworkGraph = dynamic(() => import('@/components/NetworkGraph'), { ssr: false });

function buildDecisionPoints(email: WorkspaceInsightEmail | null, insights: ReturnType<typeof deriveWorkspaceInsights>) {
  if (!email) {
    return [
      '받은편지함에서 먼저 처리할 메일을 고르면 판단 포인트를 바로 정리합니다.',
      `지금은 우선 검토 ${insights.judgmentCount}건, 조율 필요 ${insights.coordinationCount}건이 쌓여 있습니다.`,
    ];
  }

  const points: string[] = [];
  if ((email.reply_count || 0) > 1) {
    points.push(`대화가 ${email.reply_count}개 메시지로 이어져 있어 합의 상태와 다음 응답 주체를 확인해야 합니다.`);
  }
  if (email.unread) {
    points.push('아직 읽지 않은 메일이라 우선 검토 후 일정/답장 여부를 빠르게 결정해야 합니다.');
  }
  if ((email.subject || '').includes('일정') || email.snippet.includes('일정')) {
    points.push('일정 언급이 있어 바로 캘린더 반영 여부를 검토해야 합니다.');
  }

  return points.length > 0
    ? points
    : ['맥락은 안정적이지만 실행으로 연결할 다음 한 걸음을 명확히 정리하는 것이 좋습니다.'];
}

function buildExecutionItems(email: WorkspaceInsightEmail | null) {
  if (!email) {
    return ['우선 메일을 선택해 맥락과 실행 항목을 연결하세요.', '처리 대상 메일을 실행 목록으로 밀어 넣어 모바일에서도 바로 다루세요.'];
  }

  return [
    `${email.subject || '선택된 메일'} 내용을 기준으로 답장 초안을 준비합니다.`,
    '필요한 일정/후속 작업을 실행 목록으로 보내 다음 행동을 분리합니다.',
  ];
}

function SummaryCard({ title, subtitle, value, accent }: { title: string; subtitle: string; value: string; accent: 'primary' | 'emerald' | 'violet'; }) {
  const accentClass = {
    primary: 'border-primary/15 bg-primary/5 text-primary',
    emerald: 'border-emerald-500/15 bg-emerald-500/5 text-emerald-700',
    violet: 'border-violet-500/15 bg-violet-500/5 text-violet-700',
  }[accent];

  return (
    <article className={`rounded-2xl border p-4 shadow-sm ${accentClass}`}>
      <p className="text-sm font-black">{title}</p>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">{subtitle}</p>
      <p className="mt-4 text-3xl font-black tracking-tight">{value}</p>
    </article>
  );
}

function getDesktopWorkspaceMatch() {
  if (typeof window === 'undefined') return true;
  return window.matchMedia('(min-width: 1024px)').matches;
}

export default function Home() {
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null);
  const [isDesktopWorkspace, setIsDesktopWorkspace] = useState(true);
  const [summaryEmails, setSummaryEmails] = useState<WorkspaceInsightEmail[]>([]);
  const [executionQueue, setExecutionQueue] = useState<ExecutionQueueItem[]>([]);
  const [selectedContextEmail, setSelectedContextEmail] = useState<WorkspaceInsightEmail | null>(null);
  const [selectedMailboxAccountId, setSelectedMailboxAccountId] = useState<number | null>(null);
  const showMobileActions = false; // network graph hidden on mobile inbox view for simplicity
  const handleSelectEmail = (emailId: number, email?: WorkspaceInsightEmail, mailboxAccountId?: number | null) => {
    setSelectedEmail(emailId);
    setSelectedContextEmail(email ?? null);
    setSelectedMailboxAccountId(mailboxAccountId ?? null);
  };

  useEffect(() => {
    let active = true;

    const loadSummaryEmails = async () => {
      try {
        const data = await apiClient.get<{ emails: WorkspaceInsightEmail[] }>('/api/emails?limit=24');
        if (!active) return;
        setSummaryEmails(data.emails || []);
      } catch {
        if (!active) return;
        setSummaryEmails([]);
      }
    };

    void loadSummaryEmails();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const syncExecutionQueue = () => setExecutionQueue(listExecutionQueue());
    syncExecutionQueue();
    void refreshExecutionQueue().then(setExecutionQueue);
    return subscribeExecutionQueue(syncExecutionQueue);
  }, []);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(min-width: 1024px)');
    const handleChange = () => setIsDesktopWorkspace(getDesktopWorkspaceMatch());

    handleChange();
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const insights = useMemo(() => deriveWorkspaceInsights(summaryEmails), [summaryEmails]);
  const selectedSummaryEmail = useMemo(
    () => summaryEmails.find((email) => email.id === selectedEmail) ?? selectedContextEmail,
    [selectedContextEmail, selectedEmail, summaryEmails],
  );
  const decisionPoints = useMemo(() => buildDecisionPoints(selectedSummaryEmail, insights), [selectedSummaryEmail, insights]);
  const executionItems = useMemo(() => buildExecutionItems(selectedSummaryEmail), [selectedSummaryEmail]);
  const queuedItems = useMemo(() => executionQueue.filter((item) => item.status === 'queued'), [executionQueue]);
  const queuedActionCount = queuedItems.length;

  return (
    <>
      {isDesktopWorkspace ? (
        <div className="hidden h-full flex-col gap-4 lg:flex">
          <section className="grid gap-4 xl:grid-cols-[repeat(3,minmax(0,1fr))_1.2fr]">
            <SummaryCard title="오늘의 판단 포인트" subtitle="우선 검토가 필요한 메일" value={`${insights.judgmentCount}건`} accent="violet" />
            <SummaryCard title="일정 연결" subtitle="캘린더 반영 후보" value={`${insights.coordinationCount}건`} accent="primary" />
            <SummaryCard title="대기 중 작업" subtitle="바로 실행해야 할 후속" value={`${Math.max(insights.actionCount, queuedActionCount)}건`} accent="emerald" />
            <article className="rounded-2xl border border-border bg-card p-4 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-black text-foreground">빠른 실행</p>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">맥락을 바로 일정, 답장, 실행으로 넘깁니다.</p>
                </div>
                <Badge variant="secondary" className="border border-primary/10 bg-primary/10 text-primary">HOME</Badge>
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-3">
                <Link href="/ai-hub/actions" className={cn(buttonVariants({ variant: 'default' }), 'h-11 rounded-xl')}><CheckCircle2 className="mr-2 size-4" />할 일 만들기</Link>
                <Link href="/ai-hub/actions#calendar-bridge" className={cn(buttonVariants({ variant: 'outline' }), 'h-11 rounded-xl')}><CalendarDays className="mr-2 size-4" />캘린더 반영</Link>
                <Link href={selectedEmail ? `/compose?emailId=${selectedEmail}` : '/compose'} className={cn(buttonVariants({ variant: 'outline' }), 'h-11 rounded-xl')}><PenLine className="mr-2 size-4" />답장 초안</Link>
              </div>
            </article>
          </section>

          <ResizablePanelGroup orientation="horizontal" className="min-h-0 flex-1 items-stretch rounded-3xl border border-border/80 bg-card/70 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl">
            <ResizablePanel defaultSize={27} minSize={22}>
              <EmailList onSelectEmail={handleSelectEmail} selectedEmailId={selectedEmail} />
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={43} minSize={34}>
              <EmailDetail emailId={selectedEmail} mailboxAccountId={selectedMailboxAccountId} />
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={30} minSize={24}>
              <aside className="flex h-full flex-col gap-4 bg-gradient-to-b from-primary/5 via-background to-emerald-500/5 p-4">
                <section className="rounded-2xl border border-primary/15 bg-card p-4 shadow-sm">
                  <div className="flex items-center gap-2">
                    <span className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary">
                      <Network className="size-4" aria-hidden="true" />
                    </span>
                    <div>
                      <h3 className="font-black text-sm text-foreground">맥락 종합</h3>
                      <p className="text-xs text-muted-foreground">선택된 메일과 다음 행동을 한 화면에 묶습니다.</p>
                    </div>
                  </div>
                  <p className="mt-4 rounded-xl bg-primary/5 p-3 text-sm leading-6 text-foreground">
                    {selectedSummaryEmail
                      ? `${selectedSummaryEmail.subject || '선택된 메일'} · ${selectedSummaryEmail.snippet}`
                      : '메일을 고르면 요약, 판단 포인트, 실행 항목이 오른쪽 실행 보드에 정렬됩니다.'}
                  </p>
                </section>

                <section className="rounded-2xl border border-violet-500/20 bg-card p-4 shadow-sm">
                  <div className="flex items-center gap-2">
                    <span className="grid size-9 place-items-center rounded-xl bg-violet-500/10 text-violet-700">
                      <Target className="size-4" aria-hidden="true" />
                    </span>
                    <div>
                      <h3 className="font-black text-sm text-foreground">판단 포인트</h3>
                      <p className="text-xs text-muted-foreground">무엇을 먼저 결정해야 하는지 보여줍니다.</p>
                    </div>
                  </div>
                  <ul className="mt-4 space-y-2 text-sm leading-6 text-foreground">
                    {decisionPoints.map((point) => (
                      <li key={point} className="rounded-xl bg-violet-500/5 px-3 py-2">• {point}</li>
                    ))}
                  </ul>
                </section>

                <section className="rounded-2xl border border-emerald-500/20 bg-card p-4 shadow-sm">
                  <div className="flex items-center gap-2">
                    <span className="grid size-9 place-items-center rounded-xl bg-emerald-500/10 text-emerald-700">
                      <CheckCircle2 className="size-4" aria-hidden="true" />
                    </span>
                    <div>
                      <h3 className="font-black text-sm text-foreground">실행 항목</h3>
                      <p className="text-xs text-muted-foreground">결정을 바로 행동으로 넘깁니다.</p>
                    </div>
                  </div>
                  {queuedItems.length > 0 ? (
                    <ul className="mt-4 space-y-2 text-sm leading-6 text-foreground">
                      {queuedItems.slice(0, 4).map((item) => (
                        <li key={item.id} className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-3 py-2">
                          <p className="font-semibold">{item.title}</p>
                          <p className="text-xs text-muted-foreground">{item.sender} · 스와이프로 담긴 실행 항목</p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <ul className="mt-4 space-y-2 text-sm leading-6 text-foreground">
                      {executionItems.map((item) => (
                        <li key={item} className="rounded-xl bg-emerald-500/5 px-3 py-2">• {item}</li>
                      ))}
                    </ul>
                  )}
                </section>

                <section className="min-h-0 flex-1 overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
                  <div className="border-b border-border px-4 py-3">
                    <h3 className="font-black text-sm text-foreground">맥락 그래프</h3>
                    <p className="text-xs text-muted-foreground">관계와 흐름을 빠르게 훑어봅니다.</p>
                  </div>
                  <div className="h-[calc(100%-4.25rem)]">
                    <NetworkGraph />
                  </div>
                </section>
              </aside>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      ) : (
        <div className="h-full overflow-hidden rounded-3xl border border-border/80 bg-card/70 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl">
          <section
            aria-label="모바일 받은편지함"
            className={`h-full ${selectedEmail === null ? 'block' : 'hidden'}`}
          >
              <EmailList onSelectEmail={handleSelectEmail} selectedEmailId={selectedEmail} />
          </section>
          <section
            aria-label="모바일 메일 상세"
            className={`h-full flex flex-col ${selectedEmail !== null ? 'flex' : 'hidden'}`}
          >
            <div className="p-3 border-b border-border bg-card">
              <button 
                onClick={() => setSelectedEmail(null)}
                className="text-sm font-semibold text-primary flex items-center gap-1"
              >
                ← 목록으로
              </button>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              <EmailDetail emailId={selectedEmail} mailboxAccountId={selectedMailboxAccountId} />
            </div>
          </section>
          <section
            aria-label="모바일 AI 실행"
            className={`h-full ${showMobileActions ? 'flex' : 'hidden'} flex-col bg-gradient-to-b from-primary/5 via-background to-emerald-500/5 p-4`}
          >
            <div className="mb-4 rounded-2xl border border-primary/15 bg-card p-4 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Network className="size-4" aria-hidden="true" />
                </span>
                <div>
                  <h3 className="font-bold text-sm text-foreground">맥락 그래프</h3>
                  <p className="text-xs text-muted-foreground">메일과 관계의 흐름을 시각화합니다.</p>
                </div>
              </div>
            </div>
            <div className="min-h-0 flex-1 overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
              {showMobileActions && <NetworkGraph />}
            </div>
          </section>
        </div>
      )}
    </>
  );
}
