"use client";

import { useCallback, useState, useEffect } from 'react';
import { Database, FileText, HardDrive, RefreshCw, FolderOpen, CheckCircle2, Server } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

type WebdavWritebackIntentResponse = {
  intent: string;
  source_id: string | null;
  target_label: string | null;
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

type DataSurfaceStatus = 'loading' | 'ready' | 'error';

type SurfaceStatusCode = 'ready' | 'running' | 'needs_attention' | 'pending' | 'no_source';
type QualityStatusCode = 'pass' | 'needs_attention' | 'pending';
type RepositoryAssetState = 'ready' | 'needs_attention';

type DataQualitySurfaceResponse = {
  workspace_id: string;
  organization_id: string | null;
  audit_event: string;
  provider_write_executed: boolean;
  repositories: Array<{
    source_id: string;
    repository_type: 'webdav_account' | 'project_folder' | 'email_repository' | 'attachment_repository';
    display_name: string;
    object_count: number;
    writeback_enabled: boolean | null;
    evidence_source: string;
    provider_write_executed: boolean;
  }>;
  repository_assets: Array<{
    asset_key: string;
    asset_type: 'email_attachment';
    display_name: string;
    source_label: string;
    state_code: RepositoryAssetState;
    detail_text: string;
    content_chars: number;
    captured_at: string;
    evidence_source: string;
    thread_key: string;
    provider_write_executed: boolean;
  }>;
  pipeline_stages: Array<{
    stage_key: string;
    display_name: string;
    status_code: SurfaceStatusCode;
    progress_percent: number;
    evidence_source: string;
    detail_text: string;
    provider_write_executed: boolean;
  }>;
  embedding_collections: Array<{
    collection_key: string;
    display_name: string;
    object_count: number;
    embedded_count: number;
    embedding_model: string;
    vector_dimensions: number;
    status_code: SurfaceStatusCode;
    evidence_source: string;
    provider_write_executed: boolean;
  }>;
  quality_checks: Array<{
    check_key: string;
    display_name: string;
    status_code: QualityStatusCode;
    issue_count: number;
    total_count: number;
    evidence_source: string;
    detail_text: string;
    provider_write_executed: boolean;
  }>;
  connector_events: Array<{
    event_uid: string;
    signal_key: string;
    state_code: string;
    detail_text: string | null;
    observed_at: string;
  }>;
};

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

function formatCount(value: number) {
  return new Intl.NumberFormat('ko-KR').format(value);
}

function getSurfaceStatusLabel(status: SurfaceStatusCode | QualityStatusCode) {
  switch (status) {
    case 'ready':
    case 'pass':
      return '정상';
    case 'running':
      return '진행 중';
    case 'needs_attention':
      return '점검 필요';
    case 'pending':
      return '대기';
    case 'no_source':
      return '원본 없음';
    default:
      return '대기';
  }
}

function getSurfaceStatusClass(status: SurfaceStatusCode | QualityStatusCode) {
  switch (status) {
    case 'ready':
    case 'pass':
      return 'bg-emerald-100 text-emerald-700';
    case 'running':
      return 'bg-blue-100 text-blue-700';
    case 'needs_attention':
      return 'bg-amber-100 text-amber-800';
    case 'no_source':
      return 'bg-slate-100 text-slate-700';
    case 'pending':
    default:
      return 'bg-secondary text-muted-foreground';
  }
}

export function DataLayout() {
  const [activeTab, setActiveTab] = useState<'문서 저장소' | '수집 파이프라인' | '임베딩' | '품질 점검'>('문서 저장소');
  
  interface WebdavAccount {
    source_id: string;
    display_label: string;
    writeback_enabled: boolean;
    etag?: string | null;
  }
  
  interface ProjectFolder {
    folder_uid: string;
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
  const [dataSurfaceStatus, setDataSurfaceStatus] = useState<DataSurfaceStatus>('loading');
  const [dataQualitySurface, setDataQualitySurface] = useState<DataQualitySurfaceResponse | null>(null);

  useEffect(() => {
    apiClient.get<DataQualitySurfaceResponse>('/api/data/quality-surface')
      .then((data) => {
        if (!Array.isArray(data.repositories) || !Array.isArray(data.pipeline_stages)) {
          throw new Error('Invalid data quality surface response');
        }
        setDataQualitySurface(data);
        setDataSurfaceStatus('ready');
      })
      .catch((error: unknown) => {
        console.error('Data quality surface fetch error', getSafeErrorSummary(error));
        setDataQualitySurface(null);
        setDataSurfaceStatus('error');
      });

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
  const repositories = dataQualitySurface?.repositories ?? [];
  const emailRepository = repositories.find((repository) => repository.repository_type === 'email_repository');
  const attachmentRepository = repositories.find((repository) => repository.repository_type === 'attachment_repository');
  const embeddingStage = dataQualitySurface?.pipeline_stages.find((stage) => stage.stage_key === 'embedding_inventory');
  const connectorEvents = dataQualitySurface?.connector_events ?? [];
  const repositoryAssets = dataQualitySurface?.repository_assets ?? [];

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
                      <h2 className="font-bold text-sm text-muted-foreground">메일/첨부 저장소</h2>
                      <p className="text-xl font-bold">
                        {dataSurfaceStatus === 'loading' ? '확인 중' : `${formatCount(emailRepository?.object_count ?? 0)} / ${formatCount(attachmentRepository?.object_count ?? 0)}`}
                      </p>
                      <p className="mt-1 text-xs font-semibold text-muted-foreground">emails / attachments</p>
                    </div>
                  </div>
                  <div className="h-2 w-full rounded-full bg-border overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all"
                      style={{ width: `${embeddingStage?.progress_percent ?? 0}%` }}
                    ></div>
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
                            <span className="block break-all font-medium text-foreground">{account.display_label}</span>
                            <span className="block break-all text-xs text-muted-foreground">
                              {account.source_id} · {account.writeback_enabled ? 'writeback eligible' : 'read only'} · etag={account.etag ?? 'missing'}
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
                    <p className="text-lg font-bold text-emerald-600 flex items-center gap-2">
                      <CheckCircle2 className="size-5" />
                      {embeddingStage ? getSurfaceStatusLabel(embeddingStage.status_code) : dataSurfaceStatus === 'error' ? '확인 실패' : '확인 중'}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {dataQualitySurface?.audit_event ?? 'data.quality_surface.viewed'}
                    </p>
                  </div>
                  <span className="rounded-lg border border-border bg-background px-3 py-2 text-xs font-bold shadow-sm">
                    provider_write_executed={String(dataQualitySurface?.provider_write_executed ?? false)}
                  </span>
                </div>
	              </div>

              <section aria-label="문서 저장소 파일 자산" className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="flex flex-col gap-3 border-b border-border bg-secondary/30 p-5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="font-bold text-lg flex items-center gap-2"><FileText className="size-5" /> 최근 파일/첨부 자산</h2>
                    <p className="mt-1 text-sm text-muted-foreground">메일 첨부에서 파생된 문서 자산을 원본 메일/thread 근거와 함께 추적합니다.</p>
                  </div>
                  <span className="w-fit rounded-lg border border-border bg-background px-3 py-2 text-xs font-bold">
                    {formatCount(repositoryAssets.length)} assets
                  </span>
                </div>
                <div className="grid gap-3 p-4">
                  {dataSurfaceStatus === 'loading' && (
                    <p className="text-sm font-semibold text-muted-foreground">문서 자산 근거를 확인하는 중입니다.</p>
                  )}
                  {dataSurfaceStatus === 'error' && (
                    <p className="text-sm font-bold text-red-700">문서 자산 근거를 불러오지 못했습니다.</p>
                  )}
                  {dataSurfaceStatus === 'ready' && repositoryAssets.length === 0 && (
                    <p className="text-sm text-muted-foreground">이 워크스페이스에 source-linked 첨부 자산이 아직 없습니다.</p>
                  )}
                  {repositoryAssets.map((asset) => (
                    <article key={asset.asset_key} className="rounded-xl border border-border bg-background p-4">
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0">
                          <div className="flex min-w-0 items-start gap-3">
                            <FileText className="mt-0.5 size-5 shrink-0 text-primary" />
                            <div className="min-w-0">
                              <h3 className="break-all text-sm font-black">{asset.display_name}</h3>
                              <p className="mt-1 break-all text-xs text-muted-foreground">{asset.source_label}</p>
                            </div>
                          </div>
                        </div>
                        <span className={`w-fit shrink-0 rounded-full px-2 py-1 text-xs font-bold ${asset.state_code === 'ready' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-800'}`}>
                          {asset.state_code === 'ready' ? '정상' : '점검 필요'}
                        </span>
                      </div>
                      <dl className="mt-4 grid gap-3 text-xs sm:grid-cols-2 lg:grid-cols-5">
                        <div>
                          <dt className="font-black text-muted-foreground">ASSET_KEY</dt>
                          <dd className="mt-1 break-all font-mono text-[11px] font-semibold text-foreground">{asset.asset_key}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">THREAD</dt>
                          <dd className="mt-1 break-all font-mono text-[11px] font-semibold text-foreground">{asset.thread_key}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">CONTENT</dt>
                          <dd className="mt-1 text-sm font-bold">{formatCount(asset.content_chars)} chars</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">CAPTURED</dt>
                          <dd className="mt-1 break-all text-sm font-bold">{asset.captured_at}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">PROVIDER_WRITE</dt>
                          <dd className="mt-1 text-sm font-bold">{String(asset.provider_write_executed)}</dd>
                        </div>
                        <div className="min-w-0 sm:col-span-2 lg:col-span-5">
                          <dt className="font-black text-muted-foreground">EVIDENCE</dt>
                          <dd className="mt-1 break-all font-mono text-[11px] font-semibold text-muted-foreground">{asset.evidence_source} · {asset.detail_text}</dd>
                        </div>
                      </dl>
                    </article>
                  ))}
                </div>
              </section>

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
                        <dt className="font-black text-muted-foreground">TARGET_LABEL</dt>
                        <dd className="mt-1 break-all font-mono text-sm text-foreground">{writebackResult.target_label ?? 'none'}</dd>
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
                    <div key={folder.folder_uid} className="border border-border rounded-xl p-4 bg-background hover:bg-secondary/20 transition-colors">
                      <div className="flex items-center gap-3 mb-2">
                        <FolderOpen className="size-5 text-primary" />
                        <span className="font-bold truncate">{folder.project_name}</span>
                      </div>
                      <p className="mb-2 break-all font-mono text-[11px] font-semibold text-primary">{folder.folder_uid}</p>
                      <p className="text-xs text-muted-foreground break-all">{folder.webdav_path}</p>
                    </div>
                  )) : (
                    <p className="text-sm text-muted-foreground col-span-full">AI가 구조화한 프로젝트 폴더가 없습니다.</p>
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="p-5 border-b border-border bg-secondary/30">
                  <h2 className="font-bold text-lg">최근 수집/커넥터 근거</h2>
                </div>
                <div className="divide-y divide-border">
                  {dataSurfaceStatus === 'loading' && (
                    <div className="p-4 text-sm font-semibold text-muted-foreground">signed data quality surface를 확인하는 중입니다.</div>
                  )}
                  {dataSurfaceStatus === 'error' && (
                    <div className="p-4 text-sm font-bold text-red-700">데이터 품질 표면을 확인하지 못했습니다.</div>
                  )}
                  {dataSurfaceStatus === 'ready' && connectorEvents.length === 0 && (
                    <div className="p-4 text-sm text-muted-foreground">이 워크스페이스에 기록된 connector evidence가 아직 없습니다.</div>
                  )}
                  {connectorEvents.map((event) => (
                    <div key={event.event_uid} className="p-4 flex flex-col gap-3 hover:bg-secondary/10 transition-colors sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex min-w-0 items-center gap-4">
                        <div className="p-2 rounded-lg bg-blue-100 text-blue-700"><RefreshCw className="size-4" /></div>
                        <div>
                          <p className="break-all font-bold text-sm">{event.event_uid}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{event.detail_text ?? event.signal_key}</p>
                        </div>
                      </div>
                      <div className="text-left sm:text-right">
                        <span className="text-xs font-bold px-2 py-1 rounded-full bg-blue-100 text-blue-700">{event.state_code}</span>
                        <p className="text-xs text-muted-foreground mt-1">{event.observed_at}</p>
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
                  {dataSurfaceStatus === 'loading' && (
                    <p className="text-sm font-semibold text-muted-foreground">파이프라인 근거를 확인하는 중입니다.</p>
                  )}
                  {dataSurfaceStatus === 'error' && (
                    <p className="text-sm font-bold text-red-700">파이프라인 근거를 불러오지 못했습니다.</p>
                  )}
                  {dataQualitySurface?.pipeline_stages.map((stage, index) => (
                    <div key={stage.stage_key}>
                      <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <span className="text-sm font-bold">{index + 1}. {stage.display_name}</span>
                          <p className="mt-1 text-xs text-muted-foreground">{stage.detail_text}</p>
                          <p className="mt-1 break-all font-mono text-[11px] font-semibold text-muted-foreground">{stage.evidence_source}</p>
                        </div>
                        <span className={`w-fit shrink-0 rounded-full px-2 py-1 text-xs font-bold ${getSurfaceStatusClass(stage.status_code)}`}>
                          {getSurfaceStatusLabel(stage.status_code)} · {stage.progress_percent}%
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{ width: `${stage.progress_percent}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === '임베딩' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">활성 모델</p>
                  <p className="break-all text-lg font-bold text-primary">
                    {dataQualitySurface?.embedding_collections[0]?.embedding_model ?? '확인 중'}
                  </p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">벡터 차원 (Dimensions)</p>
                  <p className="text-lg font-bold">
                    {dataQualitySurface?.embedding_collections[0]?.vector_dimensions ? formatCount(dataQualitySurface.embedding_collections[0].vector_dimensions) : '-'}
                  </p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">벡터 보유 객체</p>
                  <p className="text-lg font-bold">
                    {formatCount(dataQualitySurface?.embedding_collections.reduce((sum, collection) => sum + collection.embedded_count, 0) ?? 0)}
                  </p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">대상 객체</p>
                  <p className="text-lg font-bold">
                    {formatCount(dataQualitySurface?.embedding_collections.reduce((sum, collection) => sum + collection.object_count, 0) ?? 0)}
                  </p>
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <h2 className="font-bold text-lg mb-4">임베딩 컬렉션 상태</h2>
                <div className="grid gap-3">
                  {dataSurfaceStatus === 'loading' && (
                    <p className="text-sm font-semibold text-muted-foreground">임베딩 컬렉션을 확인하는 중입니다.</p>
                  )}
                  {dataSurfaceStatus === 'error' && (
                    <p className="text-sm font-bold text-red-700">임베딩 컬렉션을 불러오지 못했습니다.</p>
                  )}
                  {dataQualitySurface?.embedding_collections.map((collection) => (
                    <article key={collection.collection_key} className="rounded-xl border border-border bg-background p-4">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <h3 className="break-all text-sm font-black">{collection.display_name}</h3>
                          <p className="mt-1 break-all font-mono text-[11px] font-semibold text-muted-foreground">{collection.evidence_source}</p>
                        </div>
                        <span className={`w-fit shrink-0 rounded-full px-2 py-1 text-xs font-bold ${getSurfaceStatusClass(collection.status_code)}`}>
                          {getSurfaceStatusLabel(collection.status_code)}
                        </span>
                      </div>
                      <dl className="mt-4 grid gap-3 text-xs sm:grid-cols-4">
                        <div>
                          <dt className="font-black text-muted-foreground">OBJECTS</dt>
                          <dd className="mt-1 text-sm font-bold">{formatCount(collection.object_count)}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">VECTORS</dt>
                          <dd className="mt-1 text-sm font-bold">{formatCount(collection.embedded_count)}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">MODEL</dt>
                          <dd className="mt-1 break-all text-sm font-bold">{collection.embedding_model}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">DIMENSIONS</dt>
                          <dd className="mt-1 text-sm font-bold">{formatCount(collection.vector_dimensions)}</dd>
                        </div>
                      </dl>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === '품질 점검' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {(dataQualitySurface?.quality_checks.slice(0, 3) ?? []).map((check) => (
                  <div key={check.check_key} className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                    <p className="text-xs font-bold text-muted-foreground mb-1">{check.display_name}</p>
                    <p className={`text-xl font-bold ${check.issue_count > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                      {formatCount(check.issue_count)} / {formatCount(check.total_count)}
                    </p>
                    <span className={`mt-3 inline-flex rounded-full px-2 py-1 text-xs font-bold ${getSurfaceStatusClass(check.status_code)}`}>
                      {getSurfaceStatusLabel(check.status_code)}
                    </span>
                  </div>
                ))}
                {dataSurfaceStatus === 'loading' && (
                  <div className="rounded-2xl border border-border bg-card p-5 text-sm font-semibold text-muted-foreground shadow-sm md:col-span-3">
                    품질 점검 근거를 확인하는 중입니다.
                  </div>
                )}
                {dataSurfaceStatus === 'error' && (
                  <div className="rounded-2xl border border-border bg-card p-5 text-sm font-bold text-red-700 shadow-sm md:col-span-3">
                    품질 점검 근거를 불러오지 못했습니다.
                  </div>
                )}
              </div>
              <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="p-5 border-b border-border bg-secondary/30">
                  <h2 className="font-bold text-lg">품질 문제 항목</h2>
                </div>
                <div className="grid gap-3 p-5">
                  {dataQualitySurface?.quality_checks.map((check) => (
                    <article key={check.check_key} className="rounded-xl border border-border bg-background p-4">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <h3 className="text-sm font-black">{check.display_name}</h3>
                          <p className="mt-1 text-sm leading-6 text-muted-foreground">{check.detail_text}</p>
                          <p className="mt-1 break-all font-mono text-[11px] font-semibold text-muted-foreground">{check.evidence_source}</p>
                        </div>
                        <span className={`w-fit shrink-0 rounded-full px-2 py-1 text-xs font-bold ${getSurfaceStatusClass(check.status_code)}`}>
                          {getSurfaceStatusLabel(check.status_code)}
                        </span>
                      </div>
                      <dl className="mt-3 grid gap-3 text-xs sm:grid-cols-3">
                        <div>
                          <dt className="font-black text-muted-foreground">ISSUES</dt>
                          <dd className="mt-1 text-sm font-bold">{formatCount(check.issue_count)}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">TOTAL</dt>
                          <dd className="mt-1 text-sm font-bold">{formatCount(check.total_count)}</dd>
                        </div>
                        <div>
                          <dt className="font-black text-muted-foreground">PROVIDER_WRITE</dt>
                          <dd className="mt-1 text-sm font-bold">provider_write_executed={String(check.provider_write_executed)}</dd>
                        </div>
                      </dl>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          )}
          
        </div>
      </main>
    </div>
  );
}
