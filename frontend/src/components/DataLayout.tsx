"use client";

import { useCallback, useState, useEffect } from 'react';
import { Database, HardDrive, RefreshCw, FolderOpen, AlertCircle, FileText, CheckCircle2, Server } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

type WebdavWritebackIntentResponse = {
  intent: string;
  source_id: string | null;
  server_url: string | null;
  requires_if_match: boolean;
  if_match?: string | null;
  provenance: string;
  status?: string | null;
  message?: string | null;
};

type WritebackStatus = 'idle' | 'loading' | 'success' | 'no_source' | 'fetch_error' | 'conflict' | 'auth' | 'error';
type WebdavAccountStatus = 'loading' | 'ready' | 'error';

type UniqueThreadIntentResponse = {
  status: string;
  candidates_checked: number;
  duplicates_found: number;
  provider_write_executed: boolean;
  provenance: string;
  audit_event: string;
  thread_updates: Array<{
    candidate_key: string;
    canonical_thread_id: string;
    dedupe_key: string;
    match_reason: 'message_id' | 'fingerprint';
    existing_message_id: string;
  }>;
};

type UniqueThreadStatus = 'idle' | 'loading' | 'success' | 'auth' | 'error';

const duplicateImportCandidates = [
  {
    candidate_key: 'zip-q2-root',
    message_id: 'q2-root@example.com',
    sender: 'partner@example.com',
    recipients: 'user@naruon.net',
    subject: 'Q2 출시 계획',
    date: '2026-05-27T09:30:00Z',
    body: 'Forwarded launch plan body',
  },
  {
    candidate_key: 'forwarded-copy',
    sender: 'partner@example.com',
    recipients: 'user@naruon.net',
    subject: 'Q2 출시 계획',
    date: '2026-05-27T09:30:00Z',
    body: 'Forwarded launch plan body',
  },
];

function getApiErrorStatus(error: unknown) {
  const shapedError = error as { status?: unknown; response?: { status?: unknown } } | null;
  if (typeof shapedError?.status === 'number') return shapedError.status;
  if (typeof shapedError?.response?.status === 'number') return shapedError.response.status;
  return null;
}

function getSafeErrorSummary(error: unknown) {
  const status = getApiErrorStatus(error);
  const errorName = error instanceof Error ? error.name : typeof error;
  return { status, error_name: errorName.slice(0, 40) };
}

export function DataLayout() {
  const [activeTab, setActiveTab] = useState<'문서 저장소' | '수집 파이프라인' | '임베딩' | '품질 점검'>('문서 저장소');
  
  interface WebdavAccount {
    source_id: string;
    server_url: string;
    username: string;
    writeback_enabled: boolean;
    etag?: string | null;
  }
  
  interface ProjectFolder {
    folder_id: number;
    project_name: string;
    webdav_path: string;
  }
  
  const [webdavAccounts, setWebdavAccounts] = useState<WebdavAccount[]>([]);
  const [webdavAccountStatus, setWebdavAccountStatus] = useState<WebdavAccountStatus>('loading');
  const [selectedWebdavSourceId, setSelectedWebdavSourceId] = useState<string | null>(null);
  const [projectFolders, setProjectFolders] = useState<ProjectFolder[]>([]);
  const [writebackStatus, setWritebackStatus] = useState<WritebackStatus>('idle');
  const [writebackResult, setWritebackResult] = useState<WebdavWritebackIntentResponse | null>(null);
  const [uniqueThreadStatus, setUniqueThreadStatus] = useState<UniqueThreadStatus>('idle');
  const [uniqueThreadResult, setUniqueThreadResult] = useState<UniqueThreadIntentResponse | null>(null);

  useEffect(() => {
    apiClient.get<WebdavAccount[]>('/api/webdav/accounts')
      .then((data) => {
        if (!Array.isArray(data)) throw new Error('Invalid WebDAV accounts response');
        setWebdavAccounts(data);
        setSelectedWebdavSourceId(data.find((account) => account.writeback_enabled)?.source_id ?? null);
        setWebdavAccountStatus('ready');
      })
      .catch((error: unknown) => {
        console.error('WebDAV accounts fetch error', getSafeErrorSummary(error));
        setWebdavAccounts([]);
        setWebdavAccountStatus('error');
        setSelectedWebdavSourceId(null);
      });

    apiClient.get<ProjectFolder[]>('/api/webdav/folders')
      .then(data => Array.isArray(data) && setProjectFolders(data))
      .catch((error: unknown) => console.error('WebDAV folders fetch error', getSafeErrorSummary(error)));
  }, []);

  const requestWebdavWritebackIntent = useCallback(async () => {
    setWritebackStatus('loading');
    setWritebackResult(null);
    try {
      if (webdavAccountStatus !== 'ready') {
        setWritebackStatus('fetch_error');
        return;
      }
      const targetSourceId = webdavAccounts.find((account) => (
        account.source_id === selectedWebdavSourceId && account.writeback_enabled
      ))?.source_id ?? webdavAccounts.find((account) => account.writeback_enabled)?.source_id;
      if (!targetSourceId) {
        setWritebackStatus('no_source');
        return;
      }
      const result = await apiClient.post<WebdavWritebackIntentResponse>(
        '/api/webdav/writeback-intent',
        { target_source_id: targetSourceId },
      );
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
  }, [selectedWebdavSourceId, webdavAccounts, webdavAccountStatus]);

  const requestUniqueThreadIntent = useCallback(async () => {
    setUniqueThreadStatus('loading');
    setUniqueThreadResult(null);
    try {
      const result = await apiClient.post<UniqueThreadIntentResponse>(
        '/api/emails/unique-thread-intent',
        { candidates: duplicateImportCandidates },
      );
      setUniqueThreadResult(result);
      setUniqueThreadStatus('success');
    } catch (error: unknown) {
      const status = getApiErrorStatus(error);
      setUniqueThreadStatus(status === 401 || status === 403 ? 'auth' : 'error');
    }
  }, []);

  const isWritebackLoading = writebackStatus === 'loading';
  const isWebdavSourceLoading = webdavAccountStatus === 'loading';
  const canRequestWebdavWriteback = webdavAccountStatus === 'ready';
  const isUniqueThreadLoading = uniqueThreadStatus === 'loading';
  const selectedWebdavAccount = webdavAccounts.find((account) => (
    account.source_id === selectedWebdavSourceId && account.writeback_enabled
  )) ?? webdavAccounts.find((account) => account.writeback_enabled) ?? null;

  return (
    <div className="flex h-full min-w-0 min-h-0 bg-background text-foreground flex-col overflow-x-hidden">
      <header className="flex h-20 shrink-0 items-center border-b border-border bg-card px-4 md:px-8 overflow-hidden">
        <h1 className="text-xl md:text-2xl font-bold flex shrink-0 items-center gap-3">
          <Database className="size-6 text-primary" /> <span className="sr-only sm:not-sr-only sm:inline">데이터와 파일</span>
        </h1>
        <p className="sr-only">중복 반입과 thread 정리</p>
        <div className="ml-4 md:ml-8 flex flex-1 min-w-0 gap-2 overflow-x-auto pb-1 scrollbar-hide">
          {['문서 저장소', '수집 파이프라인', '임베딩', '품질 점검'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as '문서 저장소' | '수집 파이프라인' | '임베딩' | '품질 점검')}
              className={`whitespace-nowrap px-3 md:px-4 py-2 text-sm font-bold rounded-lg transition-colors shrink-0 ${activeTab === tab ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-secondary'}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </header>

      <main className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden p-4 pb-[calc(7rem+env(safe-area-inset-bottom))] md:p-8 bg-background">
        <div className="max-w-5xl mx-auto space-y-8">
          
          {activeTab === '문서 저장소' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="rounded-xl bg-blue-100 p-3"><HardDrive className="size-5 text-blue-700" /></div>
                    <div>
                      <h2 className="font-bold text-sm text-muted-foreground">로컬 캐시 (Vector DB)</h2>
                      <p className="text-xl font-bold">12.4 GB <span className="text-sm font-normal text-muted-foreground">/ 50 GB</span></p>
                    </div>
                  </div>
                  <div className="h-2 w-full rounded-full bg-border overflow-hidden">
                    <div className="h-full bg-blue-500 w-[25%]"></div>
                  </div>
                </div>
                
                <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="rounded-xl bg-green-100 p-3"><FolderOpen className="size-5 text-green-700" /></div>
                    <div>
                      <h2 className="font-bold text-sm text-muted-foreground">WebDAV 원본 (연동됨)</h2>
                      <p className="text-xl font-bold">
                        {webdavAccounts.length > 0 ? `${webdavAccounts.length}개 계정` : '연결 없음'}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 grid gap-2">
                    {webdavAccounts.map((account) => {
                      const accountSelected = selectedWebdavAccount?.source_id === account.source_id;
                      return (
                        <button
                          key={account.source_id}
                          type="button"
                          disabled={!account.writeback_enabled}
                          aria-pressed={accountSelected}
                          onClick={() => setSelectedWebdavSourceId(account.source_id)}
                          className={`flex min-w-0 items-start gap-2 rounded-lg border p-2 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-70 ${
                            accountSelected ? 'border-primary bg-primary/10' : 'border-transparent bg-secondary/50 hover:border-primary/40'
                          }`}
                        >
                          <Server className="mt-0.5 size-4 shrink-0 text-primary" />
                          <span className="min-w-0">
                            <span className="block break-all font-medium text-foreground">{account.server_url}</span>
                            <span className="block break-all text-xs text-muted-foreground">
                              {account.source_id} · {account.username} · {account.writeback_enabled ? 'writeback eligible' : 'read only'} · etag={account.etag ?? 'missing'}
                            </span>
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="rounded-2xl border border-border bg-card p-6 shadow-sm flex items-center justify-between">
                  <div>
                    <h2 className="font-bold text-sm text-muted-foreground mb-1">인덱싱 상태</h2>
                    <p className="text-lg font-bold text-emerald-600 flex items-center gap-2"><CheckCircle2 className="size-5" /> 최적화됨</p>
                  </div>
                  <button className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-bold shadow-sm hover:bg-secondary">
                    수동 최적화
                  </button>
                </div>
              </div>

              <section aria-label="WebDAV writeback intent 승인" className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <p className="text-xs font-black uppercase text-primary">Customer-owned file intent</p>
                    <h2 className="mt-1 text-lg font-black">WebDAV writeback intent 승인</h2>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                      첨부파일과 AI가 구조화한 산출물은 Naruon 저장소에만 남기지 않고 고객 WebDAV 원본에 반영할 intent로 점검합니다.
                      실제 provider write는 원본 계정, If-Match 충돌 조건, provenance를 통과한 뒤 별도 실행됩니다.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void requestWebdavWritebackIntent()}
                    disabled={isWritebackLoading || !canRequestWebdavWriteback}
                    aria-busy={isWebdavSourceLoading || isWritebackLoading}
                    className="w-full whitespace-nowrap rounded-xl bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
                  >
                    WebDAV intent 승인 점검
                  </button>
                </div>

                <div role="status" aria-live="polite" className="mt-4 rounded-xl border border-border bg-background/70 p-4 text-sm">
                  {writebackStatus === 'idle' && (
                    <p className="text-muted-foreground">아직 WebDAV provider write는 실행하지 않았습니다. 원본 source와 충돌 조건만 확인합니다.</p>
                  )}
                  {writebackStatus === 'loading' && <p className="font-bold text-primary">WebDAV writeback intent 요청 중입니다.</p>}
                  {writebackStatus === 'idle' && webdavAccountStatus === 'error' && (
                    <p className="font-bold text-red-700">WebDAV 원본 계정 목록을 확인하지 못했습니다.</p>
                  )}
                  {writebackStatus === 'no_source' && (
                    <p className="font-bold text-amber-700">writeback 가능한 고객 WebDAV 원본 계정이 없어 intent를 만들 수 없습니다.</p>
                  )}
                  {writebackStatus === 'fetch_error' && (
                    <p className="font-bold text-red-700">WebDAV 원본 계정 목록을 확인하지 못해 intent를 만들 수 없습니다.</p>
                  )}
                  {writebackStatus === 'conflict' && (
                    <p className="font-bold text-red-700">If-Match/ETag 충돌이 감지되어 고객 WebDAV 원본 파일을 덮어쓰지 않았습니다.</p>
                  )}
                  {writebackStatus === 'auth' && (
                    <p className="font-bold text-red-700">signed session이 필요합니다. 공개 identity header로는 WebDAV intent를 만들 수 없습니다.</p>
                  )}
                  {writebackStatus === 'error' && (
                    <p className="font-bold text-red-700">WebDAV writeback intent 점검에 실패했습니다.</p>
                  )}
                  {writebackStatus === 'success' && writebackResult && (
                    <dl className="grid gap-3 text-xs sm:grid-cols-2 lg:grid-cols-4">
                      <div>
                        <dt className="font-black text-muted-foreground">INTENT</dt>
                        <dd className="mt-1 font-mono text-sm text-foreground">{writebackResult.intent}</dd>
                      </div>
                      <div>
                        <dt className="font-black text-muted-foreground">SOURCE_ID</dt>
                        <dd className="mt-1 font-mono text-sm text-foreground">{writebackResult.source_id ?? 'none'}</dd>
                      </div>
                      <div>
                        <dt className="font-black text-muted-foreground">IF_MATCH</dt>
                        <dd className="mt-1 font-mono text-sm text-foreground">{writebackResult.if_match ?? (writebackResult.requires_if_match ? 'required' : 'not_required')}</dd>
                      </div>
                      <div>
                        <dt className="font-black text-muted-foreground">PROVENANCE</dt>
                        <dd className="mt-1 font-mono text-sm text-foreground">{writebackResult.provenance}</dd>
                      </div>
                      <div className="min-w-0 sm:col-span-2 lg:col-span-4">
                        <dt className="font-black text-muted-foreground">SERVER_URL</dt>
                        <dd className="mt-1 break-all font-mono text-sm text-foreground">{writebackResult.server_url ?? 'none'}</dd>
                      </div>
                    </dl>
                  )}
                </div>
              </section>

              <section aria-label="unique email canonical thread intent" className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <p className="text-xs font-black uppercase text-primary">Canonical email thread</p>
                    <h2 className="mt-1 text-lg font-black">중복 메일 thread 정리 intent</h2>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                      ZIP 반입과 계정 간 포워딩으로 같은 메일이 다시 들어오면 Message-ID와 강한 body fingerprint로 기존 canonical thread에 연결할 intent를 만듭니다.
                      subject만 비슷한 메일은 자동 병합하지 않습니다.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void requestUniqueThreadIntent()}
                    disabled={isUniqueThreadLoading}
                    className="w-full whitespace-nowrap rounded-xl bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90 disabled:cursor-wait disabled:opacity-60 sm:w-auto"
                  >
                    중복 메일 thread intent 점검
                  </button>
                </div>

                <div role="status" aria-live="polite" className="mt-4 rounded-xl border border-border bg-background/70 p-4 text-sm">
                  {uniqueThreadStatus === 'idle' && (
                    <p className="text-muted-foreground">provider write나 DB 병합을 실행하지 않고 canonical thread 후보만 검증합니다.</p>
                  )}
                  {uniqueThreadStatus === 'loading' && <p className="font-bold text-primary">중복 메일 thread intent 요청 중입니다.</p>}
                  {uniqueThreadStatus === 'auth' && (
                    <p className="font-bold text-red-700">signed session이 필요합니다. 공개 identity header로는 중복 메일 intent를 만들 수 없습니다.</p>
                  )}
                  {uniqueThreadStatus === 'error' && (
                    <p className="font-bold text-red-700">중복 메일 thread intent 점검에 실패했습니다.</p>
                  )}
                  {uniqueThreadStatus === 'success' && uniqueThreadResult && (
                    <div className="space-y-3">
                      <dl className="grid gap-3 text-xs sm:grid-cols-2 lg:grid-cols-4">
                        <div>
                          <dt className="font-black text-muted-foreground">CHECKED</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">{uniqueThreadResult.candidates_checked}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">DUPLICATES</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">{uniqueThreadResult.duplicates_found}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">PROVIDER_WRITE</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">provider_write_executed={String(uniqueThreadResult.provider_write_executed)}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">AUDIT</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">{uniqueThreadResult.audit_event}</dd>
                        </div>
                      </dl>
                      <div className="grid gap-2">
                        {uniqueThreadResult.thread_updates.map((update) => (
                          <div key={update.candidate_key} className="rounded-xl border border-border bg-card p-3 text-xs">
                            <p className="font-black text-foreground">{update.candidate_key}</p>
                            <p className="mt-1 break-all text-muted-foreground">
                              {update.match_reason} → {update.canonical_thread_id} ({update.dedupe_key})
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </section>

              <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="p-5 border-b border-border bg-secondary/30">
                  <h2 className="font-bold text-lg flex items-center gap-2"><FolderOpen className="size-5" /> AI 프로젝트 구조화된 첨부파일 (WebDAV)</h2>
                </div>
                <div className="p-4 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
                  {projectFolders.length > 0 ? projectFolders.map(folder => (
                    <div key={folder.folder_id} className="border border-border rounded-xl p-4 bg-background hover:bg-secondary/20 transition-colors">
                      <div className="flex items-center gap-3 mb-2">
                        <FolderOpen className="size-5 text-primary" />
                        <span className="font-bold truncate">{folder.project_name}</span>
                      </div>
                      <p className="text-xs text-muted-foreground break-all">{folder.webdav_path}</p>
                    </div>
                  )) : (
                    <p className="text-sm text-muted-foreground col-span-full">AI가 구조화한 프로젝트 폴더가 없습니다.</p>
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="p-5 border-b border-border bg-secondary/30">
                  <h2 className="font-bold text-lg">최근 수집 로그 (Ingestion Logs)</h2>
                </div>
                <div className="divide-y divide-border">
                  {[
                    { source: '회사 IMAP', item: 'Q2 런칭 기획.pdf', status: '인덱싱 완료', time: '10분 전', icon: FileText, color: 'text-green-600 bg-green-100' },
                    { source: 'CalDAV', item: '주간 회의 일정', status: '동기화 완료', time: '1시간 전', icon: RefreshCw, color: 'text-blue-600 bg-blue-100' },
                    { source: '개인 IMAP', item: '대용량 첨부파일.zip', status: '용량 초과 (Skip)', time: '3시간 전', icon: AlertCircle, color: 'text-red-600 bg-red-100' },
                  ].map((log, i) => (
                    <div key={i} className="p-4 flex items-center justify-between hover:bg-secondary/10 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg ${log.color}`}><log.icon className="size-4" /></div>
                        <div>
                          <p className="font-bold text-sm">{log.item}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">출처: {log.source}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`text-xs font-bold px-2 py-1 rounded-full ${log.status.includes('완료') ? 'text-green-700 bg-green-100' : 'text-red-700 bg-red-100'}`}>{log.status}</span>
                        <p className="text-xs text-muted-foreground mt-1">{log.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === '수집 파이프라인' && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <h2 className="font-bold text-lg mb-6">현재 파이프라인 진행률</h2>
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-bold">1. 데이터 추출 (WebDAV / IMAP)</span>
                      <span className="text-sm text-muted-foreground font-semibold">100% 완료</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div className="h-full bg-green-500 w-full"></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-bold">2. 청크 분할 (Chunking)</span>
                      <span className="text-sm text-primary font-semibold">진행 중 (85%)</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div className="h-full bg-primary w-[85%]"></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-bold text-muted-foreground">3. 벡터 임베딩 (Embedding)</span>
                      <span className="text-sm text-muted-foreground font-semibold">대기 중</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div className="h-full bg-slate-300 w-0"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === '임베딩' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">활성 모델</p>
                  <p className="text-lg font-bold text-primary">text-embedding-3-large</p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">벡터 차원 (Dimensions)</p>
                  <p className="text-lg font-bold">3,072</p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">총 인덱싱 건수</p>
                  <p className="text-lg font-bold">28,401</p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">QPS (초당 쿼리)</p>
                  <p className="text-lg font-bold">4.2</p>
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <h2 className="font-bold text-lg mb-4">임베딩 컬렉션 상태</h2>
                <div className="divide-y divide-border border border-border rounded-lg overflow-hidden">
                  <div className="grid grid-cols-4 bg-secondary/50 p-3 text-xs font-bold text-muted-foreground">
                    <div>컬렉션 명</div>
                    <div>청크 수</div>
                    <div>마지막 업데이트</div>
                    <div>상태</div>
                  </div>
                  <div className="grid grid-cols-4 p-3 text-sm items-center">
                    <div className="font-bold">emails_naruon</div>
                    <div>12,400</div>
                    <div className="text-muted-foreground">10분 전</div>
                    <div><span className="bg-green-100 text-green-700 px-2 py-0.5 rounded text-xs font-bold">정상</span></div>
                  </div>
                  <div className="grid grid-cols-4 p-3 text-sm items-center">
                    <div className="font-bold">docs_webdav</div>
                    <div>16,001</div>
                    <div className="text-muted-foreground">1시간 전</div>
                    <div><span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-bold">업데이트 중</span></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === '품질 점검' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">인덱싱 실패</p>
                  <p className="text-xl font-bold text-red-500">23건</p>
                  <button className="mt-3 text-xs font-semibold text-primary hover:underline">재시도</button>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">고아(Orphaned) 청크</p>
                  <p className="text-xl font-bold text-orange-500">105건</p>
                  <button className="mt-3 text-xs font-semibold text-primary hover:underline">정리하기</button>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">임베딩 일치율 평균</p>
                  <p className="text-xl font-bold text-green-600">92.4%</p>
                  <button className="mt-3 text-xs font-semibold text-primary hover:underline">상세 리포트</button>
                </div>
              </div>
              <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="p-5 border-b border-border bg-secondary/30">
                  <h2 className="font-bold text-lg">품질 문제 항목</h2>
                </div>
                <div className="p-5 text-sm text-muted-foreground text-center">
                  발견된 심각한 데이터 품질 문제가 없습니다.
                </div>
              </div>
            </div>
          )}
          
        </div>
      </main>
    </div>
  );
}
