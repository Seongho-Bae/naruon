"use client";

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Settings, Plus, Users, Video, Paperclip, Clock, CalendarDays, X } from 'lucide-react';

import { apiClient } from '@/lib/api-client';

type CalendarWritebackIntentResponse = {
  workspace_id: string;
  target_source_id: string;
  protocol: string;
  writeback_mode: 'customer_owned';
  requires_if_match: boolean;
  if_match: string | null;
  provenance: Record<string, string>;
  audit_event: string;
};

type CalendarWritebackSource = {
  source_id: string;
  provider: string;
  protocol: 'caldav' | 'carddav' | 'webdav' | 'local';
  owner_id: string;
  organization_id: string | null;
  capabilities: string[];
  writeback_enabled: boolean;
  etag: string | null;
};

type WritebackStatus = 'idle' | 'loading' | 'success' | 'no_source' | 'conflict' | 'auth' | 'error';

const calendarList = [
  { name: '김나루 (나)', swatchClassName: 'bg-primary' },
  { name: 'Naruon PM 팀', swatchClassName: 'bg-red-500' },
  { name: '제품 개발팀', swatchClassName: 'bg-green-500' },
  { name: '마케팅팀', swatchClassName: 'bg-purple-500' },
  { name: '회사 공용', swatchClassName: 'bg-indigo-500' },
  { name: '공휴일', swatchClassName: 'bg-slate-400' },
] as const;

function isCustomerOwnedWritableSource(source: CalendarWritebackSource) {
  return source.writeback_enabled
    && source.protocol !== 'local'
    && source.capabilities.includes('write');
}

function getApiErrorStatus(error: unknown) {
  const shapedError = error as { status?: unknown; response?: { status?: unknown } } | null;
  if (typeof shapedError?.status === 'number') return shapedError.status;
  if (typeof shapedError?.response?.status === 'number') return shapedError.response.status;
  return null;
}

export function CalendarLayout() {
  const [viewMode, setViewMode] = useState<'월간 캘린더' | '주간 캘린더' | '일정 상세' | '회의 조율' | '일정 후보'>('월간 캘린더');
  const [writebackStatus, setWritebackStatus] = useState<WritebackStatus>('idle');
  const [writebackResult, setWritebackResult] = useState<CalendarWritebackIntentResponse | null>(null);
  const [writebackSources, setWritebackSources] = useState<CalendarWritebackSource[]>([]);
  const [sourceLoadStatus, setSourceLoadStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    void apiClient.get<CalendarWritebackSource[]>('/api/calendar/writeback-sources')
      .then((sources) => {
        if (!isMounted) return;
        setWritebackSources(sources);
        setSelectedSourceId(sources.find(isCustomerOwnedWritableSource)?.source_id ?? null);
        setSourceLoadStatus('ready');
      })
      .catch(() => {
        if (!isMounted) return;
        setWritebackSources([]);
        setSourceLoadStatus('error');
        setSelectedSourceId(null);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const selectedWritebackSource = useMemo(() => {
    const selectedSource = writebackSources.find((source) => source.source_id === selectedSourceId);
    if (selectedSource && isCustomerOwnedWritableSource(selectedSource)) return selectedSource;
    return writebackSources.find(isCustomerOwnedWritableSource) ?? null;
  }, [selectedSourceId, writebackSources]);
  const isSourceRegistryReady = sourceLoadStatus === 'ready';

  const requestWritebackIntent = useCallback(async (action: 'create' | 'update') => {
    if (!isSourceRegistryReady) {
      setWritebackResult(null);
      setWritebackStatus(sourceLoadStatus === 'error' ? 'error' : 'loading');
      return;
    }
    if (selectedWritebackSource === null) {
      setWritebackResult(null);
      setWritebackStatus('no_source');
      return;
    }
    setWritebackStatus('loading');
    setWritebackResult(null);
    try {
      const result = await apiClient.post<CalendarWritebackIntentResponse>('/api/calendar/writeback-intent', {
        action,
        summary: action === 'create'
          ? 'Naruon 일정 후보 writeback intent 점검'
          : 'Naruon 기존 일정 ETag/If-Match 충돌 점검',
        ...(selectedWritebackSource ? { target_source_id: selectedWritebackSource.source_id } : {}),
      });
      setWritebackResult(result);
      setWritebackStatus('success');
    } catch (error: unknown) {
      const status = getApiErrorStatus(error);
      if (status === 422) {
        setWritebackStatus('no_source');
      } else if (status === 409) {
        setWritebackStatus('conflict');
      } else if (status === 401 || status === 403) {
        setWritebackStatus('auth');
      } else {
        setWritebackStatus('error');
      }
    }
  }, [isSourceRegistryReady, selectedWritebackSource, sourceLoadStatus]);

  const isWritebackLoading = writebackStatus === 'loading';
  const isWritebackActionDisabled = isWritebackLoading || !isSourceRegistryReady;

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground">
      {/* Left Sidebar - Calendar List */}
      <aside className="w-64 shrink-0 flex-col overflow-y-auto border-r border-border bg-card p-4 hidden lg:flex">
        <button type="button" aria-label="새 일정 만들기" className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2.5 text-sm font-bold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">
          <Plus className="size-4" aria-hidden="true" />새 일정
        </button>

        <div className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xs font-bold text-muted-foreground">캘린더 목록</h2>
          </div>
          <ul className="space-y-3">
            {calendarList.map((cal) => (
              <li key={cal.name} className="flex items-center gap-3 text-sm">
                <input type="checkbox" defaultChecked className="size-4 rounded border-border accent-primary text-primary focus:ring-primary" />
                <span className={`size-2.5 shrink-0 rounded-full ${cal.swatchClassName}`} aria-hidden="true" />
                <span className="font-medium text-foreground">{cal.name}</span>
              </li>
            ))}
          </ul>
          <button type="button" aria-label="새 캘린더 계정 추가" className="mt-4 flex items-center gap-2 text-sm font-semibold text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">
            <Plus className="size-4" aria-hidden="true" /> 캘린더 추가
          </button>
        </div>
      </aside>

      {/* Main Calendar Area */}
      <main className="flex min-w-0 flex-1 flex-col bg-background">
        <header className="flex h-auto min-h-16 shrink-0 flex-col items-start gap-3 border-b border-border bg-card px-4 py-3 lg:px-6">
          <div className="flex min-w-0 flex-wrap items-center gap-3 lg:gap-4">
            <button type="button" className="rounded-md border border-border bg-background px-3 py-1.5 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">오늘</button>
            <div className="flex items-center gap-1">
              <button type="button" aria-label="이전 달" className="grid size-8 place-items-center rounded-md hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"><ChevronLeft className="size-5" /></button>
              <button type="button" aria-label="다음 달" className="grid size-8 place-items-center rounded-md hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"><ChevronRight className="size-5" /></button>
            </div>
            <h1 className="text-xl font-bold">일정 관리</h1>
            <h2 className="text-sm font-bold text-muted-foreground lg:ml-2">2026년 5월</h2>
          </div>
          <div className="flex w-full min-w-0 items-center gap-3">
            <div className="flex min-w-0 overflow-x-auto rounded-md border border-border">
              {['월간 캘린더', '주간 캘린더', '일정 상세', '회의 조율', '일정 후보'].map((mode) => (
                <button type="button"
                  key={mode}
                  onClick={() => setViewMode(mode as '월간 캘린더' | '주간 캘린더' | '일정 상세' | '회의 조율' | '일정 후보')}
                  className={`shrink-0 px-4 py-1.5 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 ${viewMode === mode ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-secondary'}`}
                >
                  {mode}
                </button>
              ))}
            </div>
            <button type="button" aria-label="설정" className="grid size-9 shrink-0 place-items-center rounded-md border border-border bg-background hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">
              <Settings className="size-5" />
            </button>
          </div>
        </header>

        <div className="flex-1 space-y-5 overflow-y-auto p-4 pb-[calc(7rem+env(safe-area-inset-bottom))] md:p-6 lg:pb-6">
          <p className="sr-only">원본 계정 writeback 흐름</p>
          <section aria-label="CalDAV writeback intent 점검" className="rounded-2xl border border-border bg-card p-4 shadow-sm md:p-5">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="min-w-0">
                <p className="text-xs font-black uppercase text-primary">Customer-owned calendar intent</p>
                <h2 className="mt-1 text-lg font-black text-foreground">CalDAV/CardDAV/WebDAV writeback intent</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                  Naruon은 캘린더 서버가 아니라 고객 원본 계정에 반영할 의도를 기록합니다.
                  실제 provider write는 source capability, provenance, ETag/If-Match, 감사 이벤트를 통과해야 합니다.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void requestWritebackIntent('create')}
                  disabled={isWritebackActionDisabled}
                  title={isWritebackActionDisabled ? "원본 계정을 불러오거나 점검 중입니다" : "새 일정을 생성하는 intent를 점검합니다"}
                  className="rounded-xl bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90 disabled:cursor-wait disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
                >
                  새 일정 intent 점검
                </button>
                <button
                  type="button"
                  onClick={() => void requestWritebackIntent('update')}
                  disabled={isWritebackActionDisabled}
                  title={isWritebackActionDisabled ? "원본 계정을 불러오거나 점검 중입니다" : "기존 일정을 수정하는 ETag 업데이트 intent를 점검합니다"}
                  className="rounded-xl border border-border bg-background px-4 py-2 text-sm font-bold hover:bg-secondary disabled:cursor-wait disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
                >
                  ETag 업데이트 점검
                </button>
              </div>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {writebackSources.map((source) => {
                const sourceWritable = isCustomerOwnedWritableSource(source);
                const sourceSelected = selectedWritebackSource?.source_id === source.source_id;
                return (
                  <button
                    key={source.source_id}
                    type="button"
                    disabled={!sourceWritable}
                    aria-pressed={sourceSelected}
                    onClick={() => setSelectedSourceId(source.source_id)}
                    title={!sourceWritable ? "쓰기 권한이 없는 계정입니다" : `${source.provider} 선택`}
                    className={`rounded-xl border p-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-70 ${
                      sourceSelected
                        ? 'border-primary bg-primary/10 shadow-sm'
                        : 'border-border bg-background/70 hover:border-primary/40'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="font-mono text-xs font-bold text-primary">{source.source_id}</p>
                        <p className="mt-1 break-words text-sm font-bold">{source.provider}</p>
                      </div>
                      <span className={`rounded-full px-2 py-1 text-xs font-black ${sourceWritable ? 'bg-green-100 text-green-700' : 'bg-secondary text-muted-foreground'}`}>
                        {sourceSelected ? 'selected' : sourceWritable ? 'write' : 'read_only'}
                      </span>
                    </div>
                    <p className="mt-2 text-xs font-semibold text-muted-foreground">
                      {source.protocol} · {source.capabilities.join(', ')}
                    </p>
                    <p className="mt-2 break-all font-mono text-[11px] font-semibold text-muted-foreground">
                      etag={source.etag ?? 'missing'} · writeback={sourceWritable ? 'eligible' : 'blocked'}
                    </p>
                  </button>
                );
              })}
              {sourceLoadStatus === 'ready' && writebackSources.length === 0 && (
                <p className="rounded-xl border border-border bg-background/70 p-3 text-sm font-bold text-amber-700">
                  연결된 CalDAV/CardDAV/WebDAV source가 없습니다.
                </p>
              )}
              {sourceLoadStatus === 'loading' && (
                <p className="rounded-xl border border-border bg-background/70 p-3 text-sm font-bold text-primary">
                  CalDAV source registry 확인 중입니다.
                </p>
              )}
              {sourceLoadStatus === 'error' && (
                <p className="rounded-xl border border-border bg-background/70 p-3 text-sm font-bold text-amber-700">
                  signed session으로 CalDAV source registry를 확인할 수 없습니다.
                </p>
              )}
            </div>

            <div role="status" aria-live="polite" className="mt-4 rounded-xl border border-border bg-background/70 p-4 text-sm">
              {writebackStatus === 'idle' && (
                <p className="text-muted-foreground">아직 provider write는 실행하지 않았습니다. intent 점검으로 원본 source와 충돌 조건만 확인합니다.</p>
              )}
              {writebackStatus === 'loading' && <p className="font-bold text-primary">writeback intent 요청 중입니다.</p>}
              {writebackStatus === 'no_source' && (
                <p className="font-bold text-amber-700">원본 CalDAV/CardDAV/WebDAV 계정이 없어 writeback intent를 만들 수 없습니다.</p>
              )}
              {writebackStatus === 'conflict' && (
                <p className="font-bold text-red-700">ETag/If-Match 충돌이 감지되어 원본 일정을 덮어쓰지 않았습니다.</p>
              )}
              {writebackStatus === 'auth' && (
                <p className="font-bold text-red-700">signed session이 필요합니다. 공개 헤더로는 writeback intent를 만들 수 없습니다.</p>
              )}
              {writebackStatus === 'error' && (
                <p className="font-bold text-red-700">writeback intent 점검에 실패했습니다.</p>
              )}
              {writebackStatus === 'success' && writebackResult && (
                <dl className="grid gap-3 text-xs sm:grid-cols-2 2xl:grid-cols-3">
                  <div>
                    <dt className="font-black text-muted-foreground">WRITEBACK_MODE</dt>
                    <dd className="mt-1 font-mono text-sm text-foreground">{writebackResult.writeback_mode}</dd>
                  </div>
                  <div>
                    <dt className="font-black text-muted-foreground">PROTOCOL</dt>
                    <dd className="mt-1 font-mono text-sm text-foreground">{writebackResult.protocol}</dd>
                  </div>
                  <div>
                    <dt className="font-black text-muted-foreground">TARGET_SOURCE</dt>
                    <dd className="mt-1 font-mono text-sm text-foreground">{writebackResult.target_source_id}</dd>
                  </div>
                  <div>
                    <dt className="font-black text-muted-foreground">IF_MATCH</dt>
                    <dd className="mt-1 font-mono text-sm text-foreground">{writebackResult.if_match ?? 'not_required'}</dd>
                  </div>
                  <div>
                    <dt className="font-black text-muted-foreground">AUDIT_EVENT</dt>
                    <dd className="mt-1 font-mono text-sm text-foreground">{writebackResult.audit_event}</dd>
                  </div>
                </dl>
              )}
            </div>
          </section>

          {viewMode === '월간 캘린더' && (
            <div className="h-full rounded-2xl border border-border bg-card shadow-sm flex flex-col overflow-hidden">
              <div className="grid grid-cols-7 border-b border-border bg-secondary/50 text-center text-sm font-semibold py-3">
                <div className="text-red-500">일</div><div>월</div><div>화</div><div>수</div><div>목</div><div>금</div><div className="text-blue-500">토</div>
              </div>
              <div className="grid grid-cols-7 grid-rows-5 flex-1 divide-x divide-y divide-border">
                {/* Simulated Grid Cells */}
                {Array.from({ length: 35 }).map((_, i) => (
                  <div key={i} className="min-h-[84px] p-2 sm:min-h-[100px]">
                    <span className={`text-sm font-semibold ${i % 7 === 0 ? 'text-red-500' : i % 7 === 6 ? 'text-blue-500' : 'text-muted-foreground'}`}>{i < 31 ? i + 1 : ''}</span>
                    {i === 15 && (
                      <div className="mt-1 rounded bg-green-100 px-1.5 py-1 text-[10px] font-semibold leading-tight text-green-700 sm:px-2 sm:text-xs">
                        10:00<span className="hidden sm:inline"> 제품 리뷰</span>
                      </div>
                    )}
                    {i === 22 && (
                      <div className="mt-1 rounded bg-orange-100 px-1.5 py-1 text-[10px] font-semibold leading-tight text-orange-700 sm:px-2 sm:text-xs">
                        09:30<span className="hidden sm:inline"> 출시 회의</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          {viewMode === '주간 캘린더' && (
            <section aria-label="주간 캘린더" className="rounded-2xl border border-border bg-card p-5 shadow-sm">
              <h3 className="text-lg font-bold">주간 캘린더</h3>
              <div className="mt-4 grid gap-3 md:grid-cols-5">
                {[
                  ['월', '제품 리뷰', 'caldav-primary'],
                  ['화', '파트너 미팅 후보', 'caldav-sales'],
                  ['수', '리소스 배정 검토', 'caldav-team'],
                  ['목', '출시 회의', 'caldav-primary'],
                  ['금', '마케팅 캠페인 오프', 'caldav-marketing'],
                ].map(([day, title, source]) => (
                  <article key={day} className="rounded-xl border border-border bg-background p-4">
                    <p className="text-xs font-black text-primary">{day}</p>
                    <h4 className="mt-2 text-sm font-bold">{title}</h4>
                    <p className="mt-2 font-mono text-xs text-muted-foreground">{source}</p>
                  </article>
                ))}
              </div>
            </section>
          )}
          {viewMode === '일정 상세' && (
            <section aria-label="일정 상세" className="rounded-2xl border border-border bg-card p-5 shadow-sm">
              <h3 className="text-lg font-bold">출시 회의 상세</h3>
              <dl className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-background p-4">
                  <dt className="text-xs font-black text-muted-foreground">원본 계정</dt>
                  <dd className="mt-2 text-sm font-bold">Customer CalDAV · caldav-primary</dd>
                </div>
                <div className="rounded-xl border border-border bg-background p-4">
                  <dt className="text-xs font-black text-muted-foreground">충돌 제어</dt>
                  <dd className="mt-2 text-sm font-bold">ETag / If-Match 필요 시 server-authoritative 검증</dd>
                </div>
              </dl>
            </section>
          )}
          {viewMode === '회의 조율' && (
            <div className="flex h-full flex-col gap-4">
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <h3 className="text-lg font-bold mb-4">회의 조율 (Coordination)</h3>
                <p className="text-sm text-muted-foreground mb-4">참석자들의 캘린더(CalDAV)를 종합 분석하여 최적의 시간을 제안합니다.</p>
                <div className="grid gap-3 max-w-lg">
                  <button type="button" className="flex items-center justify-between rounded-xl border border-primary/20 bg-primary/5 p-4 hover:bg-primary/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">
                    <div className="flex items-center gap-3">
                      <span className="grid size-8 place-items-center rounded-lg bg-primary/20 text-primary font-bold">1안</span>
                      <div className="text-left">
                        <p className="font-bold">5월 23일 (목) 14:00 - 15:00</p>
                        <p className="text-xs text-muted-foreground">모든 참석자 참석 가능</p>
                      </div>
                    </div>
                    <span className="text-xs font-bold text-primary">제안하기</span>
                  </button>
                  <button type="button" className="flex items-center justify-between rounded-xl border border-border bg-card p-4 hover:bg-secondary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">
                    <div className="flex items-center gap-3">
                      <span className="grid size-8 place-items-center rounded-lg bg-secondary text-muted-foreground font-bold">2안</span>
                      <div className="text-left">
                        <p className="font-bold">5월 24일 (금) 10:00 - 11:00</p>
                        <p className="text-xs text-muted-foreground">1명(김개발) 불참 예상</p>
                      </div>
                    </div>
                    <span className="text-xs font-bold text-muted-foreground">제안하기</span>
                  </button>
                </div>
              </div>
            </div>
          )}
          {viewMode === '일정 후보' && (
            <section aria-label="일정 후보" className="rounded-2xl border border-border bg-card p-5 shadow-sm">
              <h3 className="text-lg font-bold">일정 후보</h3>
              <div className="mt-4 grid gap-3 lg:grid-cols-3">
                {[
                  ['파트너 미팅 일정 확정', 'Customer CalDAV', 'create intent'],
                  ['출시 회의 시간 변경', 'Team CalDAV', 'update intent + If-Match'],
                  ['개인 메일에서 발견된 회사 일정', 'Company CalDAV', 'source reassignment'],
                ].map(([title, source, mode]) => (
                  <article key={title} className="rounded-xl border border-border bg-background p-4">
                    <h4 className="text-sm font-bold">{title}</h4>
                    <p className="mt-2 text-xs text-muted-foreground">{source}</p>
                    <p className="mt-3 rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">{mode}</p>
                  </article>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>

      {/* Right Sidebar - Event Detail */}
      <aside className="w-[340px] shrink-0 flex-col overflow-y-auto border-l border-border bg-card p-5 hidden xl:flex">
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <span className="rounded-md bg-orange-100 px-2 py-1 text-xs font-bold text-orange-700">★ 중요</span>
            <span className="rounded-md bg-secondary px-2 py-1 text-xs font-bold text-muted-foreground">공개</span>
          </div>
          <div className="flex items-center gap-2">
            <button type="button" aria-label="닫기" className="grid size-8 place-items-center rounded-md hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"><X className="size-4" /></button>
          </div>
        </div>

        <div className="mt-6">
          <div className="flex items-center gap-3">
            <div className="size-4 rounded-full bg-orange-500"></div>
            <h2 className="text-xl font-bold">출시 회의 (Naruon 2.0)</h2>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">Naruon 2.0 출시 준비 및 일정 공유</p>
        </div>

        <div className="mt-6 space-y-5">
          <div className="flex gap-3">
            <Clock className="size-5 text-muted-foreground shrink-0" />
            <div>
              <p className="text-sm font-semibold">2026.05.23 (목) 09:30 - 11:00</p>
              <p className="text-xs text-muted-foreground">1시간 30분</p>
            </div>
          </div>
          <div className="flex gap-3 items-center">
            <Video className="size-5 text-muted-foreground shrink-0" />
            <p className="text-sm font-semibold">회의실 A (4층)</p>
            <button type="button" className="text-xs text-primary font-semibold ml-auto hover:underline rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">위치 보기</button>
          </div>
          <div className="flex gap-3 items-start">
            <Users className="size-5 text-muted-foreground shrink-0" />
            <div>
              <p className="text-sm font-semibold mb-2">참석자 6명</p>
              <div className="flex -space-x-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="size-8 rounded-full border-2 border-card bg-slate-200"></div>
                ))}
                <div className="flex size-8 items-center justify-center rounded-full border-2 border-card bg-secondary text-xs font-bold">+2</div>
              </div>
            </div>
          </div>
          <div className="flex gap-3 items-start">
            <CalendarDays className="size-5 text-muted-foreground shrink-0" />
            <div>
              <p className="text-sm font-semibold mb-1">설명</p>
              <p className="text-sm text-muted-foreground">Naruon 2.0 출시 전 최종 점검 및 공유, 각 파트별 일정 및 역할 확인.</p>
            </div>
          </div>
          <div className="flex gap-3 items-start">
            <Paperclip className="size-5 text-muted-foreground shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-semibold mb-2">첨부파일 <span className="text-muted-foreground font-normal">2개</span></p>
              <div className="space-y-2">
                <div className="flex items-center justify-between rounded-lg border border-border bg-background p-2">
                  <span className="text-xs font-semibold">Naruon_2.0_런칭계획.pptx</span>
                  <span className="text-xs text-muted-foreground">2.4 MB</span>
                </div>
                <div className="flex items-center justify-between rounded-lg border border-border bg-background p-2">
                  <span className="text-xs font-semibold">출시_체크리스트.xlsx</span>
                  <span className="text-xs text-muted-foreground">1.1 MB</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 flex gap-3">
          <button type="button" className="flex-1 rounded-lg border border-border bg-background py-2 text-sm font-bold shadow-sm hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">삭제</button>
          <button type="button" className="flex-1 rounded-lg border border-border bg-background py-2 text-sm font-bold shadow-sm hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">복사</button>
          <button type="button" className="flex-1 rounded-lg bg-primary py-2 text-sm font-bold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40">수정</button>
        </div>
      </aside>
    </div>
  );
}
