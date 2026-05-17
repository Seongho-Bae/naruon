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
              <span className="shrink-0 rounded-full bg-primary/10 px-2 py-1 text-[11px] font-bold text-primary">{formatStartupDate(result.date)}</span>
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
  const { results, status } = useStartupSearch('판단 대기 캘린더 반영 실행 항목', 3);

  return (
    <section
      aria-label="오늘의 실행 대시보드"
      className="h-full overflow-y-auto rounded-3xl border border-border/80 bg-gradient-to-br from-primary/8 via-card to-emerald-500/8 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]"
    >
      <div className="max-w-5xl space-y-6">
        <div className="rounded-3xl border border-primary/15 bg-card/90 p-6 shadow-sm">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">Naruon Start</p>
          <h1 className="mt-3 text-3xl font-black text-foreground">오늘의 실행 대시보드</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
            메일, 일정, 실행 항목을 한 번에 훑고 지금 필요한 작업공간으로 바로 이동합니다.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => onOpenView('email')}
              className="inline-flex h-11 items-center gap-2 rounded-2xl bg-primary px-4 text-sm font-bold text-primary-foreground shadow-[0_16px_34px_rgba(37,99,255,0.28)] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
            >
              <Inbox className="size-4" aria-hidden="true" />
              이메일 작업공간 열기
            </button>
            <button
              type="button"
              onClick={() => onOpenView('calendar')}
              className="inline-flex h-11 items-center gap-2 rounded-2xl border border-border bg-background px-4 text-sm font-bold text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
            >
              <CalendarDays className="size-4 text-primary" aria-hidden="true" />
              일정관리 열기
            </button>
          </div>
        </div>
        <div className="rounded-3xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-2xl bg-primary/10 text-primary"><CheckCircle2 className="size-5" aria-hidden="true" /></span>
            <div>
              <h2 className="text-base font-black text-foreground">실시간 실행 후보</h2>
              <p className="text-sm leading-6 text-muted-foreground">검색 API에서 오늘 처리할 메일과 일정 후보를 불러옵니다.</p>
            </div>
          </div>
        </div>
        {status === 'loading' ? <div role="status" className="rounded-3xl border border-border bg-card p-5 text-sm font-semibold text-muted-foreground shadow-sm">대시보드 후보를 불러오는 중입니다.</div> : null}
        {status === 'error' ? <div role="alert" className="rounded-3xl border border-destructive/30 bg-destructive/10 p-5 text-sm font-semibold text-destructive shadow-sm">대시보드 후보를 불러오지 못했습니다.</div> : null}
        {status === 'empty' ? <div className="rounded-3xl border border-border bg-card p-5 text-sm font-semibold text-muted-foreground shadow-sm">오늘 표시할 실행 후보가 없습니다.</div> : null}
        {status === 'success' ? <StartupResultList results={results} /> : null}
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

export default function Home() {
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
  const startupView = useWorkspaceStartupView();
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
    const syncMobileWorkspaceOverride = () => {
      setMobileWorkspaceOverride(window.location.hash.startsWith('#mobile-'));
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
            className={`mobile-workspace-panel mobile-workspace-panel-search h-full ${effectiveMobileView === 'search' ? 'flex' : 'hidden'} flex-col overflow-y-auto bg-gradient-to-b from-primary/5 via-background to-card p-4 pb-28`}
          >
            {effectiveMobileView === 'search' ? <MobileSearchPanel /> : null}
          </section>
          <section
            id="mobile-actions"
            aria-label="모바일 AI 실행"
            role="region"
            className={`mobile-workspace-panel mobile-workspace-panel-actions h-full ${effectiveMobileView === 'actions' ? 'flex' : 'hidden'} flex-col overflow-y-auto bg-gradient-to-b from-primary/5 via-background to-emerald-500/5 p-4 pb-28`}
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
            className={`mobile-workspace-panel mobile-workspace-panel-calendar h-full ${effectiveMobileView === 'calendar' ? 'flex' : 'hidden'} flex-col overflow-y-auto bg-gradient-to-b from-primary/5 via-background to-card p-4 pb-28`}
          >
            {effectiveMobileView === 'calendar' ? <MobileCalendarPanel /> : null}
          </section>
      </div>
    </>
  );
}
