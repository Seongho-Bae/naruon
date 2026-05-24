"use client";

import { useEffect, useRef, useState } from 'react';

import { EmailList } from '@/components/EmailList';
import { EmailDetail } from '@/components/EmailDetail';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import dynamic from 'next/dynamic';
import { CalendarDays, CheckCircle2, Inbox, Network } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { setMobileWorkspaceView, useMobileWorkspaceView } from '@/lib/mobile-workspace';
import { toSafeReactText } from '@/lib/safe-text';
import { useWorkspaceStartupView, type WorkspaceStartupView } from '@/lib/workspace-preferences';
import { MobileCalendarPanel, MobileSearchPanel } from '@/components/mobile-workspace-panels';
const NetworkGraph = dynamic(() => import('@/components/NetworkGraph'), { ssr: false });

type WorkspaceActionCommand = { id: number; action: string; target: 'desktop' | 'tablet'; modeVersion: number };
type MobileActionCommand = { id: number; action: string; modeVersion: number };
type StartupSearchResult = {
  id: number;
  subject: string | null;
  sender: string;
  date: string;
  snippet: string;
};

function useStartupSearch(query: string, limit: number) {
  const [status, setStatus] = useState<'loading' | 'success' | 'empty' | 'error'>('loading');
  const [results, setResults] = useState<StartupSearchResult[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;
    void apiClient.post<{ results: StartupSearchResult[] }>('/api/search', { query, limit }, { signal: controller.signal })
      .then((response) => {
        if (cancelled) return;
        setResults(response.results);
        setStatus(response.results.length > 0 ? 'success' : 'empty');
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setResults([]);
        setStatus('error');
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [limit, query]);

  return { results, status };
}

type TaskItem = {
  id: string;
  title: string;
  status: 'open' | 'in_progress' | 'blocked' | 'done';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  created_at: string;
  updated_at: string;
};

interface EmailItem {
  id: number;
  subject: string | null;
  sender: string;
  date?: string;
  snippet: string;
  unread?: boolean;
}

function useDashboardData() {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<{ emails: EmailItem[] }>('/api/emails').catch(() => ({ emails: [] })),
      apiClient.get<TaskItem[]>('/api/tasks').catch(() => [])
    ]).then(([emailRes, tasksRes]) => {
      if (cancelled) return;
      setEmails(emailRes.emails || []);
      setTasks(tasksRes || []);
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  return { emails, tasks, loading };
}

function formatStartupDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '날짜 미정';
  return new Intl.DateTimeFormat('ko-KR', { month: 'short', day: 'numeric' }).format(date);
}

function StartupResultList({ results }: { results: StartupSearchResult[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {results.map((result) => {
        const subject = toSafeReactText(result.subject?.trim() || null, '(제목 없음)');
        const sender = toSafeReactText(result.sender);
        const snippet = toSafeReactText(result.snippet);
        return (
          <article key={result.id} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-base font-black text-foreground">{subject}</h2>
              <span suppressHydrationWarning className="shrink-0 rounded-full bg-primary/10 px-2 py-1 text-[11px] font-bold text-primary">{formatStartupDate(result.date)}</span>
            </div>
            <p className="mt-1 text-xs font-bold text-primary">{sender}</p>
            <p className="mt-3 line-clamp-3 text-sm leading-6 text-muted-foreground">{snippet}</p>
          </article>
        );
      })}
    </div>
  );
}

function StartupDashboard({ onOpenView }: { onOpenView: (view: WorkspaceStartupView) => void }) {
  const { emails, tasks, loading } = useDashboardData();
  const unreadCount = emails.filter((e) => e.unread).length;
  const pendingTasks = tasks.filter((t) => t.status !== 'done');
  
  const mapPriorityToKorean = (p: string) => {
    switch(p) {
      case 'urgent': return '긴급';
      case 'high': return '높음';
      case 'normal': return '보통';
      case 'low': return '낮음';
      default: return p;
    }
  };
  return (
    <section role="region" aria-label="홈 개요 대시보드" className="h-full overflow-y-auto bg-background p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        
        {/* Header Section */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">안녕하세요, 김나루님 👋</h1>
          </div>
          <div className="flex items-center gap-4">
            <span suppressHydrationWarning className="text-sm font-medium text-muted-foreground">2026.05.25 (토) 오전 10:23</span>
            <button className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-1.5 text-sm font-medium hover:bg-accent hover:text-accent-foreground">
              <span className="grid size-4 place-items-center"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 20v-8m0 0V4m0 8h8m-8 0H4" strokeLinecap="round" strokeLinejoin="round"/></svg></span>
              홈 설정
            </button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-5 gap-4">
          {[
            { title: '받은 메일', value: loading ? '-' : emails.length.toString(), diff: unreadCount > 0 ? `+${unreadCount}` : '-', diffText: '안 읽음', icon: Inbox, color: 'text-primary' },
            { title: '오늘 일정', value: '5', diff: '+1', diffText: '어제 대비', icon: CalendarDays, color: 'text-blue-500' },
            { title: '대기 중 작업', value: loading ? '-' : pendingTasks.length.toString(), diff: '-', diffText: '변동 없음', icon: CheckCircle2, color: 'text-green-500' },
            { title: '진행 중 프로젝트', value: '7', diff: '-', diffText: '변동 없음', icon: Network, color: 'text-purple-500' },
            { title: '이번 주 목표 진행률', value: '68%', diff: '+6%', diffText: '지난주 대비', icon: CheckCircle2, color: 'text-emerald-500' },
          ].map((stat, i) => (
            <div key={i} className="rounded-2xl border border-border bg-card p-4 shadow-sm">
              <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                <stat.icon className={`size-4 ${stat.color}`} />
                {stat.title}
              </div>
              <div className="mt-4 text-3xl font-bold">{stat.value}</div>
              <div className={`mt-2 text-xs font-medium ${stat.diff.startsWith('+') ? 'text-primary' : stat.diff.startsWith('-') && stat.diff !== '-' ? 'text-red-500' : 'text-muted-foreground'}`}>
                {stat.diff} <span className="text-muted-foreground font-normal">{stat.diffText}</span>
              </div>
            </div>
          ))}
        </div>

        {/* 오늘의 핵심 요약 */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
          <h2 className="text-lg font-bold">오늘의 핵심 요약</h2>
          <div className="mt-4 grid grid-cols-3 gap-6 divide-x divide-border">
            <div className="flex gap-4">
              <div className="grid size-10 shrink-0 place-items-center rounded-full bg-purple-100 text-purple-600"><Inbox className="size-5" /></div>
              <div>
                <p className="font-bold">중요 메일 {loading ? '-' : unreadCount}건</p>
                <p className="text-xs text-muted-foreground mt-1">오늘 확인이 필요한 메일이 있어요.</p>
                <button onClick={() => onOpenView('email')} className="mt-2 text-xs font-semibold text-primary hover:underline">메일 바로가기</button>
              </div>
            </div>
            <div className="flex gap-4 pl-6">
              <div className="grid size-10 shrink-0 place-items-center rounded-full bg-blue-100 text-blue-600"><CalendarDays className="size-5" /></div>
              <div>
                <p className="font-bold">회의 2건 예정</p>
                <p className="text-xs text-muted-foreground mt-1">오전 10:30, 오후 14:00</p>
                <button onClick={() => onOpenView('calendar')} className="mt-2 text-xs font-semibold text-primary hover:underline">일정 확인하기</button>
              </div>
            </div>
            <div className="flex gap-4 pl-6">
              <div className="grid size-10 shrink-0 place-items-center rounded-full bg-green-100 text-green-600"><CheckCircle2 className="size-5" /></div>
              <div>
                <p className="font-bold">완료 가능 작업 {loading ? '-' : pendingTasks.length}건</p>
                <p className="text-xs text-muted-foreground mt-1">오늘 마감 전 완료해보세요.</p>
                <button className="mt-2 text-xs font-semibold text-primary hover:underline">작업 바로가기</button>
              </div>
            </div>
          </div>
        </div>

        {/* Middle Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold">오늘의 판단 포인트</h2>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-lg bg-secondary/50 p-3">
                <div className="flex items-center gap-3">
                  <span className="rounded bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-700">우선 검토 필요</span>
                  <div>
                    <p className="text-sm font-bold">출시 회의 (Naruon 2.0)</p>
                    <p className="text-[11px] text-muted-foreground">주요 의사결정이 필요한 회의입니다.</p>
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">오늘 10:30</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-secondary/50 p-3">
                <div className="flex items-center gap-3">
                  <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">데이터 검토</span>
                  <div>
                    <p className="text-sm font-bold">5월 리포트 분석</p>
                    <p className="text-[11px] text-muted-foreground">핵심 지표 변동사항을 확인하세요.</p>
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">오늘 11:00</span>
              </div>
            </div>
            <button className="mt-4 w-full text-center text-sm font-semibold text-primary hover:underline">오늘 전체 보기</button>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold">대기 중 작업 {pendingTasks.length > 0 && <span className="ml-2 rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">{pendingTasks.length}건</span>}</h2>
            </div>
            <div className="space-y-3">
              {loading ? (
                <div className="text-sm text-muted-foreground p-2">작업을 불러오는 중...</div>
              ) : pendingTasks.length === 0 ? (
                <div className="text-sm text-muted-foreground p-2">대기 중인 작업이 없습니다.</div>
              ) : pendingTasks.slice(0, 3).map((task) => {
                const pKor = mapPriorityToKorean(task.priority);
                const pClass = pKor === '긴급' || pKor === '높음' ? 'text-red-500' : pKor === '보통' ? 'text-green-500' : 'text-muted-foreground';
                return (
                  <div key={task.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <input type="checkbox" className="size-4 rounded border-border text-primary" />
                      <span className="text-sm font-medium">{task.title}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className={`font-semibold ${pClass}`}>{pKor}</span>
                    </div>
                  </div>
                );
              })}
            </div>
            <button className="mt-4 w-full text-center text-sm font-semibold text-primary hover:underline">전체 작업 보기</button>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold">일정 충돌 알림 <span className="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">3건</span></h2>
            </div>
            <div className="space-y-3">
              {[
                { time: '10:30', title: '출시 회의', location: '회의실 A', conflict: '충돌' },
                { time: '14:00', title: '고객 미팅', location: '회의실 B', conflict: '중복' },
              ].map((cal, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="font-bold text-red-500 w-12">{cal.time}</div>
                  <div className="flex-1">
                    <div className="flex justify-between">
                      <p className="text-sm font-bold">{cal.title}</p>
                      <span className="rounded bg-orange-100 px-1.5 py-0.5 text-[10px] font-bold text-orange-700">{cal.conflict}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{cal.location}</p>
                  </div>
                </div>
              ))}
            </div>
            <button className="mt-4 w-full text-center text-sm font-semibold text-primary hover:underline">일정 조정하기</button>
          </div>
        </div>

        {/* Bottom Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          <div className="lg:col-span-2 rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold">최근 메일 {unreadCount > 0 && <span className="ml-2 rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">새 메일 {unreadCount}</span>}</h2>
            </div>
            <div className="space-y-3">
              {loading ? (
                <div className="text-sm text-muted-foreground p-2">메일을 불러오는 중...</div>
              ) : emails.length === 0 ? (
                <div className="text-sm text-muted-foreground p-2">수신된 메일이 없습니다.</div>
              ) : emails.slice(0, 5).map((mail) => (
                <div key={mail.id} className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="size-8 shrink-0 rounded-full bg-secondary grid place-items-center font-bold text-xs">
                      {toSafeReactText(mail.sender).charAt(0).toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1 flex items-center gap-2">
                      <span className="text-sm font-bold truncate w-32 shrink-0">{toSafeReactText(mail.sender)}</span>
                      <span className="text-sm font-bold truncate">{toSafeReactText(mail.subject, '(제목 없음)')}</span>
                      <span className="text-sm text-muted-foreground truncate hidden lg:inline">{toSafeReactText(mail.snippet)}</span>
                    </div>
                  </div>
                  <div suppressHydrationWarning className="flex items-center gap-2 shrink-0 text-xs text-muted-foreground">
                    {formatStartupDate(mail.date || '')}
                    {mail.unread && <span className="size-2 rounded-full bg-primary" />}
                  </div>
                </div>
              ))}
            </div>
            <button onClick={() => onOpenView('email')} className="mt-4 w-full text-center text-sm font-semibold text-primary hover:underline">메일함 바로가기</button>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold">빠른 실행</h2>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: '새 메일 작성', icon: Inbox, color: 'text-blue-500' },
                { label: '일정 추가', icon: CalendarDays, color: 'text-blue-500' },
                { label: '새 프로젝트', icon: Network, color: 'text-purple-500' },
                { label: '작업 만들기', icon: CheckCircle2, color: 'text-green-500' },
                { label: 'AI 허브로 이동', icon: Network, color: 'text-purple-500' },
                { label: '데이터 대시보드', icon: Network, color: 'text-purple-500' },
                { label: '문서 작성', icon: CheckCircle2, color: 'text-blue-500' },
                { label: '파일 업로드', icon: Network, color: 'text-blue-500' },
              ].map((action, i) => (
                <button key={i} className="flex items-center justify-start gap-3 rounded-xl border border-border bg-card px-4 py-3 text-xs font-bold hover:bg-secondary transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
                  <action.icon className={`size-5 shrink-0 ${action.color}`} />
                  <span className="truncate">{action.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}

function StartupCalendar({ onOpenView }: { onOpenView: (view: WorkspaceStartupView) => void }) {
  const { results, status } = useStartupSearch('회의 마감 후속 조치 일정', 3);

  return (
    <section aria-label="일정관리 시작 화면" className="h-full overflow-y-auto rounded-3xl border border-border/80 bg-card/80 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
      <div className="max-w-4xl space-y-5">
        <div className="rounded-3xl border border-primary/15 bg-primary/5 p-6">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">Calendar</p>
          <h1 className="mt-3 text-3xl font-black text-foreground">일정관리 시작 화면</h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">메일에서 추출한 회의, 마감, 후속 조치를 먼저 확인합니다.</p>
          <button
            type="button"
            onClick={() => onOpenView('email')}
            className="mt-5 inline-flex h-11 items-center gap-2 rounded-2xl bg-primary px-4 text-sm font-bold text-primary-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
          >
            <Inbox className="size-4" aria-hidden="true" />
            이메일 작업공간 열기
          </button>
        </div>
        {status === 'loading' ? <div role="status" className="rounded-2xl border border-border bg-card px-4 py-3 text-sm font-semibold text-muted-foreground shadow-sm">일정 후보를 불러오는 중입니다.</div> : null}
        {status === 'error' ? <div role="alert" className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm font-semibold text-destructive shadow-sm">일정 후보를 불러오지 못했습니다.</div> : null}
        {status === 'empty' ? <div className="rounded-2xl border border-border bg-card px-4 py-3 text-sm font-semibold text-muted-foreground shadow-sm">일정 후보가 없습니다.</div> : null}
        {status === 'success' ? <StartupResultList results={results} /> : null}
      </div>
    </section>
  );
}

export function WorkspaceHome({ forcedStartupView }: { forcedStartupView?: WorkspaceStartupView } = {}) {
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null);
  const [workspaceActionNotice, setWorkspaceActionNotice] = useState<string | null>(null);
  const [desktopDetailActionCommand, setDesktopDetailActionCommand] = useState<WorkspaceActionCommand | null>(null);
  const [mobileDetailActionCommand, setMobileDetailActionCommand] = useState<MobileActionCommand | null>(null);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [isTabletViewport, setIsTabletViewport] = useState(false);
  const [viewportReady, setViewportReady] = useState(false);
  const [mobileViewportModeVersion, setMobileViewportModeVersion] = useState(0);
  const [desktopViewportModeVersion, setDesktopViewportModeVersion] = useState(0);
  const mobileViewportModeRef = useRef(isMobileViewport);
  const desktopViewportModeRef = useRef(false);
  const storedStartupView = useWorkspaceStartupView();
  const startupView = forcedStartupView ?? storedStartupView;
  const [startupViewOverride, setStartupViewOverride] = useState<WorkspaceStartupView | null>(null);
  const [mobileWorkspaceOverride, setMobileWorkspaceOverride] = useState(false);
  const [mobileWorkspaceOverrideReady, setMobileWorkspaceOverrideReady] = useState(false);
  const activeStartupView = startupViewOverride ?? startupView;
  const showMobileDashboard = activeStartupView === 'dashboard' && mobileWorkspaceOverrideReady && !mobileWorkspaceOverride;

  const mobileView = useMobileWorkspaceView();
  const effectiveMobileView = mobileView === 'detail' && selectedEmail === null ? 'inbox' : mobileView;
  const openStartupView = (view: WorkspaceStartupView) => {
    setStartupViewOverride(view);
    setMobileWorkspaceOverride(view !== 'dashboard');
    if (view === 'email') {
      setMobileWorkspaceView('inbox', { updateHash: false });
    }
    if (view === 'calendar') {
      setMobileWorkspaceView('calendar', { updateHash: false });
    }
  };
  const handleSelectEmail = (emailId: number) => {
    setStartupViewOverride('email');
    setSelectedEmail(emailId);
    setWorkspaceActionNotice(null);
    setDesktopDetailActionCommand(null);
    setMobileDetailActionCommand(null);
    if (typeof window !== 'undefined' && window.matchMedia?.('(max-width: 1023px)').matches) {
      setMobileWorkspaceView('detail');
    }
  };

  useEffect(() => {
    const mediaQuery = window.matchMedia?.('(max-width: 1023px)');
    if (!mediaQuery) {
      const markViewportReady = () => setViewportReady(true);
      markViewportReady();
      return;
    }

    const syncViewport = () => {
      if (mobileViewportModeRef.current !== mediaQuery.matches) {
        mobileViewportModeRef.current = mediaQuery.matches;
        setMobileViewportModeVersion((version) => version + 1);
        setDesktopViewportModeVersion((version) => version + 1);
      }
      setIsMobileViewport(mediaQuery.matches);
      setViewportReady(true);
    };
    syncViewport();
    mediaQuery.addEventListener('change', syncViewport);
    return () => mediaQuery.removeEventListener('change', syncViewport);
  }, []);

  useEffect(() => {
    const mediaQuery = window.matchMedia?.('(min-width: 1024px) and (max-width: 1279px)');
    if (!mediaQuery) return;

    const syncViewport = () => {
      if (desktopViewportModeRef.current !== mediaQuery.matches) {
        desktopViewportModeRef.current = mediaQuery.matches;
        setDesktopViewportModeVersion((version) => version + 1);
      }
      setIsTabletViewport(mediaQuery.matches);
    };
    syncViewport();
    mediaQuery.addEventListener('change', syncViewport);
    return () => mediaQuery.removeEventListener('change', syncViewport);
  }, []);

  useEffect(() => {
    if (window.location.hash.startsWith('#mobile-')) {
      return;
    }
    if (startupView === 'calendar') {
      setMobileWorkspaceView('calendar', { updateHash: false });
    }
    if (startupView === 'email') {
      setMobileWorkspaceView('inbox', { updateHash: false });
    }
  }, [startupView]);

  useEffect(() => {
    const clearStartupOverride = () => setStartupViewOverride(null);
    window.addEventListener('naruon:startup-view-change', clearStartupOverride);
    return () => window.removeEventListener('naruon:startup-view-change', clearStartupOverride);
  }, []);

  useEffect(() => {
    const syncMobileWorkspaceOverride = (event?: Event) => {
      const eventView = event instanceof CustomEvent ? (event as CustomEvent<{ view?: string }>).detail?.view : null;
      const hasExplicitWorkspaceOverride = typeof eventView === 'string' && eventView !== 'inbox';
      setMobileWorkspaceOverride(window.location.hash.startsWith('#mobile-') || hasExplicitWorkspaceOverride);
      setMobileWorkspaceOverrideReady(true);
    };
    syncMobileWorkspaceOverride();
    const clearMobileWorkspaceOverride = () => {
      setMobileWorkspaceOverride(false);
      setMobileWorkspaceOverrideReady(true);
    };
    window.addEventListener('hashchange', syncMobileWorkspaceOverride);
    window.addEventListener('naruon:mobile-workspace', syncMobileWorkspaceOverride);
    window.addEventListener('naruon:startup-view-change', clearMobileWorkspaceOverride);
    return () => {
      window.removeEventListener('hashchange', syncMobileWorkspaceOverride);
      window.removeEventListener('naruon:mobile-workspace', syncMobileWorkspaceOverride);
      window.removeEventListener('naruon:startup-view-change', clearMobileWorkspaceOverride);
    };
  }, []);

  useEffect(() => {
    function handleHeaderAction(event: Event) {
      const action = (event as CustomEvent<{ action?: string }>).detail?.action;
      if (!action) return;

      if (selectedEmail === null) {
        setWorkspaceActionNotice('먼저 메일을 선택하세요.');
        return;
      }

      setWorkspaceActionNotice(null);
      if (isMobileViewport) {
        setMobileDetailActionCommand((previous) => ({ id: (previous?.id ?? 0) + 1, action, modeVersion: mobileViewportModeVersion }));
        setMobileWorkspaceView('detail');
      } else {
        setDesktopDetailActionCommand((previous) => ({
          id: (previous?.id ?? 0) + 1,
          action,
          target: isTabletViewport ? 'tablet' : 'desktop',
          modeVersion: desktopViewportModeVersion,
        }));
      }
    }

    window.addEventListener('naruon:header-action', handleHeaderAction);
    return () => window.removeEventListener('naruon:header-action', handleHeaderAction);
  }, [desktopViewportModeVersion, isMobileViewport, isTabletViewport, mobileViewportModeVersion, selectedEmail]);

  return (
    <>
      {workspaceActionNotice && (
        <div role="status" aria-live="polite" className="absolute left-1/2 top-3 z-50 -translate-x-1/2 rounded-2xl border border-primary/20 bg-card px-4 py-3 text-sm font-bold text-primary shadow-lg">
          {workspaceActionNotice}
        </div>
      )}
      {activeStartupView === 'dashboard' && viewportReady && !isMobileViewport && <div className="hidden h-full lg:block"><StartupDashboard onOpenView={openStartupView} /></div>}
      {activeStartupView === 'calendar' && viewportReady && !isMobileViewport && <div className="hidden h-full lg:block"><StartupCalendar onOpenView={openStartupView} /></div>}
      <section role="region" aria-label="데스크톱 메일 작업공간" className={`${activeStartupView === 'email' ? 'hidden xl:block' : 'hidden'} h-full`}>
        {viewportReady && !isMobileViewport && !isTabletViewport ? (
        <ResizablePanelGroup orientation="horizontal" className="h-full items-stretch rounded-3xl border border-border/80 bg-card/70 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl">
          <ResizablePanel defaultSize={27} minSize={22}>
            <EmailList onSelectEmail={handleSelectEmail} selectedEmailId={selectedEmail} />
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={48} minSize={34}>
            <EmailDetail emailId={selectedEmail} actionCommand={desktopDetailActionCommand?.target === 'desktop' && desktopDetailActionCommand.modeVersion === desktopViewportModeVersion ? desktopDetailActionCommand : null} />
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={25} minSize={20}>
            <div className="h-full flex flex-col bg-gradient-to-b from-primary/5 via-background to-emerald-500/5 p-4">
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
              <div className="flex-1 overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
                <NetworkGraph />
              </div>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
        ) : null}
      </section>
      <section
        role="region"
        aria-label="태블릿 메일 작업공간"
        className={`${activeStartupView === 'email' ? 'hidden lg:flex xl:hidden' : 'hidden'} h-full min-h-0 gap-3 rounded-3xl border border-border/80 bg-card/70 p-3 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl`}
      >
        {viewportReady && isTabletViewport ? (
          <>
        <div className="min-w-0 basis-[38%] overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
          <EmailList onSelectEmail={handleSelectEmail} selectedEmailId={selectedEmail} />
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-3 overflow-hidden">
          <div className="min-h-0 flex-1 overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
            <EmailDetail emailId={selectedEmail} actionCommand={desktopDetailActionCommand?.target === 'tablet' && desktopDetailActionCommand.modeVersion === desktopViewportModeVersion ? desktopDetailActionCommand : null} />
          </div>
          <details aria-label="태블릿 맥락 그래프" className="shrink-0 rounded-2xl border border-primary/15 bg-gradient-to-r from-primary/5 via-card to-emerald-500/5 shadow-sm">
            <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-black text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
              <span className="flex items-center gap-2">
                <span className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Network className="size-4" aria-hidden="true" />
                </span>
                태블릿 맥락 패널
              </span>
              <span className="text-xs font-semibold text-muted-foreground">필요할 때 펼치기</span>
            </summary>
            <div className="border-t border-border/70 p-4">
              <p className="mb-3 text-xs font-semibold text-muted-foreground">맥락 그래프는 필요할 때 펼쳐서 확인합니다.</p>
              <div className="h-80 overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
                <NetworkGraph />
              </div>
            </div>
          </details>
        </div>
          </>
        ) : null}
      </section>
       {showMobileDashboard && <div className="h-full lg:hidden"><StartupDashboard onOpenView={openStartupView} /></div>}
       <div className={`${showMobileDashboard ? 'hidden' : 'block'} h-full overflow-hidden rounded-3xl border border-border/80 bg-card/70 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl lg:hidden`}>
          <section
            id="mobile-inbox"
            aria-label="모바일 받은편지함"
            role="region"
            className={`mobile-workspace-panel mobile-workspace-panel-inbox h-full ${effectiveMobileView === 'inbox' ? 'block' : 'hidden'}`}
          >
            <EmailList onSelectEmail={handleSelectEmail} selectedEmailId={selectedEmail} />
          </section>
          <section
            id="mobile-detail"
            aria-label="모바일 메일 상세"
            role="region"
            className={`mobile-workspace-panel h-full flex-col ${effectiveMobileView === 'detail' && selectedEmail !== null ? 'flex' : 'hidden'}`}
          >
            <div className="p-3 border-b border-border bg-card">
              <button
                onClick={() => {
                  setSelectedEmail(null);
                  setMobileDetailActionCommand(null);
                  setMobileWorkspaceView('inbox');
                }}
                className="text-sm font-semibold text-primary flex items-center gap-1"
              >
                ← 목록으로
              </button>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              {viewportReady && isMobileViewport && effectiveMobileView === 'detail' && selectedEmail !== null ? <EmailDetail emailId={selectedEmail} actionCommand={mobileDetailActionCommand?.modeVersion === mobileViewportModeVersion ? mobileDetailActionCommand : null} /> : null}
            </div>
          </section>
          <section
            id="mobile-search"
            aria-label="모바일 맥락 검색"
            role="region"
            className={`mobile-workspace-panel mobile-workspace-panel-search h-full ${effectiveMobileView === 'search' ? 'flex' : 'hidden'} flex-col overflow-y-auto bg-gradient-to-b from-primary/5 via-background to-card p-4 pb-[calc(7rem+env(safe-area-inset-bottom))]`}
          >
            {effectiveMobileView === 'search' ? <MobileSearchPanel /> : null}
          </section>
          <section
            id="mobile-actions"
            aria-label="모바일 AI 실행"
            role="region"
            className={`mobile-workspace-panel mobile-workspace-panel-actions h-full ${effectiveMobileView === 'actions' ? 'flex' : 'hidden'} flex-col overflow-y-auto bg-gradient-to-b from-primary/5 via-background to-emerald-500/5 p-4 pb-[calc(7rem+env(safe-area-inset-bottom))]`}
          >
            <div className="mb-4 rounded-2xl border border-primary/15 bg-card p-4 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Network className="size-4" aria-hidden="true" />
                </span>
                <div>
                  <h3 className="font-bold text-sm text-foreground">관계 맥락</h3>
                  <p className="text-xs text-muted-foreground">메일과 관계의 흐름을 시각화합니다.</p>
                </div>
              </div>
            </div>
            <div className="min-h-0 flex-1 overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
              {effectiveMobileView === 'actions' && <NetworkGraph />}
            </div>
          </section>
          <section
            id="mobile-calendar"
            aria-label="모바일 일정 연결"
            role="region"
            className={`mobile-workspace-panel mobile-workspace-panel-calendar h-full ${effectiveMobileView === 'calendar' ? 'flex' : 'hidden'} flex-col overflow-y-auto bg-gradient-to-b from-primary/5 via-background to-card p-4 pb-[calc(7rem+env(safe-area-inset-bottom))]`}
          >
            {effectiveMobileView === 'calendar' ? <MobileCalendarPanel /> : null}
          </section>
      </div>
    </>
  );
}

export default WorkspaceHome;
