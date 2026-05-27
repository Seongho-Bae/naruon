"use client";

import { Activity, Settings, User, Mail, Bell, Shield, Smartphone, Plus, Monitor, AlertCircle, RefreshCw } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useWorkspaceStartupView, setWorkspaceStartupView } from '@/lib/workspace-preferences';
import { useEffect, useState } from 'react';

type SettingsTab = '워크스페이스' | '멤버' | '연결 계정' | '알림' | '자동화' | '결제' | '개발자';

interface RunnerConfig {
  workspace_id: string;
  configured: boolean;
  fingerprint: string | null;
  updated_at: string | null;
  connector_manifest: {
    role: string;
    network_mode: string;
    control_plane_domain: string;
    local_protocols: string[];
    prohibited_roles: string[];
    runner_usage: string;
  };
}

interface OperationalSignal {
  signal_key: string;
  display_name: string;
  state: string;
  evidence_source: string;
  detail: string;
  provider_write_executed: boolean;
}

interface ConnectorSignalEvent {
  event_uid: string;
  signal_key: string;
  state_code: string;
  detail_text: string | null;
  observed_at: string;
}

interface OperationalSignalsResponse {
  workspace_id: string;
  audit_event: string;
  telemetry: {
    prometheus_metrics_enabled: boolean;
    otel_traces_enabled: boolean;
    otel_endpoint_configured: boolean;
    otel_endpoint_host: string | null;
  };
  connector: {
    workspace_id: string;
    registration_state: 'registration_configured' | 'not_registered';
    connection_state: 'connected' | 'not_connected';
    active_connection_count: number;
    control_plane_domain: string;
    network_mode: string;
    runner_usage: string;
    local_protocols: string[];
    last_heartbeat_at: string | null;
    last_disconnect_at: string | null;
    queue_depth_state: 'not_reported';
    recent_events: ConnectorSignalEvent[];
  };
  signals: OperationalSignal[];
}

const settingsTabs: { id: SettingsTab; icon: typeof Monitor }[] = [
  { id: '워크스페이스', icon: Monitor },
  { id: '멤버', icon: User },
  { id: '연결 계정', icon: Mail },
  { id: '알림', icon: Bell },
  { id: '자동화', icon: Settings },
  { id: '결제', icon: Shield },
  { id: '개발자', icon: Smartphone },
];

const settingsDetailSurfaces: Partial<Record<SettingsTab, {
  heading: string;
  copy: string;
  items: { title: string; detail: string; status: string }[];
}>> = {
  멤버: {
    heading: '멤버와 역할',
    copy: '조직 관리자, 보안 담당자, 팀 리드, 개인 사용자의 역할과 ABAC 조건을 한 화면에서 점검합니다.',
    items: [
      { title: '관리자 경계', detail: 'platform_admin과 organization_admin 권한을 분리하고 customer-policy deny를 우선 적용합니다.', status: 'RBAC/ABAC' },
      { title: '팀 스코프', detail: '그룹/본부/팀 단위 멤버십과 workspace scope를 감사 로그와 함께 추적합니다.', status: '조직 계층' },
      { title: '초대 검토', detail: '외부 공유와 신규 초대는 보안 정책, consent, data-region 조건을 통과해야 합니다.', status: '정책 점검' },
    ],
  },
  알림: {
    heading: '알림 정책',
    copy: '메일 회신 추적, 일정 충돌, writeback conflict, connector health 이벤트를 사용자별 채널 정책으로 정리합니다.',
    items: [
      { title: '답변 추적', detail: '보낸 메일 SLA가 지연되면 홈 대기 작업과 알림 큐에 같은 사건으로 표시합니다.', status: '메일 연동' },
      { title: '일정 충돌', detail: 'CalDAV writeback 후보가 충돌하거나 ETag가 맞지 않으면 재확인 알림을 생성합니다.', status: '캘린더' },
      { title: 'Connector health', detail: 'self-hosted connector heartbeat, sync lag, provider throttling을 운영 알림으로 묶습니다.', status: '운영' },
    ],
  },
  자동화: {
    heading: '자동화 규칙',
    copy: '메일, 일정, 할 일, 프로젝트 상태를 source-linked rule로 연결하되 provider write는 명시적 intent로 남깁니다.',
    items: [
      { title: '메일에서 작업 생성', detail: '실행 항목을 ticket task로 만들고 원본 message/thread provenance를 유지합니다.', status: 'source-linked' },
      { title: '캘린더 writeback', detail: 'AI가 정리한 일정은 source capability와 owner policy를 확인한 뒤 원천 계정에 반영합니다.', status: 'intent-first' },
      { title: '지식 정리', detail: '내가 나에게 보낸 메일은 개인 지식 후보로 분류하고 연결 프로젝트를 제안합니다.', status: 'knowledge' },
    ],
  },
  결제: {
    heading: '결제와 사용량',
    copy: 'B2C, SOHO, 조직 계정이 같은 tenant 구조에서 quota, connector, AI 사용량을 분리해 봅니다.',
    items: [
      { title: '워크스페이스 quota', detail: '메일 본문 저장소가 아니라 metadata/index/action intent 중심으로 사용량을 계산합니다.', status: 'data sovereignty' },
      { title: 'Connector seat', detail: '사내망 connector는 조직 스코프별 등록 토큰과 운영 감사 대상으로 계산합니다.', status: 'B2B2C' },
      { title: 'AI 사용량', detail: '프롬프트 실행, 평가, 요약, writeback 제안을 provider별 비용 항목으로 분리합니다.', status: 'BYOK' },
    ],
  },
};

export function SettingsLayout() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('워크스페이스');
  const [runnerConfig, setRunnerConfig] = useState<RunnerConfig | null>(null);
  const [runnerError, setRunnerError] = useState<string | null>(null);
  const [runnerLoading, setRunnerLoading] = useState(true);
  const [operationalSignals, setOperationalSignals] = useState<OperationalSignalsResponse | null>(null);
  const [operationalError, setOperationalError] = useState<string | null>(null);
  const [operationalLoading, setOperationalLoading] = useState(true);
  const startupView = useWorkspaceStartupView();
  const connectorManifest = runnerConfig?.connector_manifest;
  const detailSurface = settingsDetailSurfaces[activeTab];
  const connectorEvents = operationalSignals?.connector.recent_events ?? [];

  useEffect(() => {
    let cancelled = false;

    void apiClient
      .get<RunnerConfig>('/api/runner-config')
      .then((config) => {
        if (cancelled) return;
        setRunnerConfig(config);
        setRunnerError(null);
      })
      .catch((error: Error) => {
        if (cancelled) return;
        setRunnerError(error.message || 'Self-hosted connector 설정을 불러오지 못했습니다.');
      })
      .finally(() => {
        if (!cancelled) setRunnerLoading(false);
      });

    void apiClient
      .get<OperationalSignalsResponse>('/api/observability/operational-signals')
      .then((signals) => {
        if (cancelled) return;
        setOperationalSignals(signals);
        setOperationalError(null);
      })
      .catch((error: Error) => {
        if (cancelled) return;
        setOperationalError(error.message || '운영 신호를 불러오지 못했습니다.');
      })
      .finally(() => {
        if (!cancelled) setOperationalLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex h-full min-w-0 min-h-0 bg-background text-foreground flex-col overflow-x-hidden">
      <header className="flex h-20 shrink-0 items-center border-b border-border bg-card px-4 md:px-8 overflow-hidden">
        <h1 className="text-xl md:text-2xl font-bold flex shrink-0 items-center gap-3">
          <Settings className="size-6 text-primary" />
          <span className="sm:hidden">설정</span>
          <span className="hidden sm:inline">설정 (Settings)</span>
        </h1>
        <p className="sr-only">Self-hosted Runner</p>
      </header>

      <nav aria-label="설정 섹션" className="md:hidden border-b border-border bg-card px-3 py-2">
        <div className="flex gap-2 overflow-x-auto pb-1">
          {settingsTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`min-h-10 shrink-0 rounded-xl px-4 text-sm font-bold transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
                activeTab === tab.id
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-background text-muted-foreground hover:bg-secondary hover:text-foreground'
              }`}
            >
              {tab.id}
            </button>
          ))}
        </div>
      </nav>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left Sidebar - Settings Tabs */}
        <aside className="w-64 shrink-0 border-r border-border bg-card overflow-y-auto hidden md:block">
          <div className="p-4 space-y-1">
            {settingsTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-colors ${activeTab === tab.id ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-secondary hover:text-foreground'}`}
              >
                <tab.icon className="size-4" /> {tab.id}
              </button>
            ))}
          </div>
        </aside>

        {/* Main Settings Area */}
        <main className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden p-4 md:p-8 bg-background">
          <div className="max-w-3xl space-y-8">
            
            {activeTab === '워크스페이스' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-bold text-xl">워크스페이스 설정</h2>
                    <p className="text-sm text-muted-foreground mt-1">Naruon의 전반적인 동작과 시작 화면을 설정합니다.</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                    <h3 className="font-bold text-lg mb-4">시작 화면 설정</h3>
                    <p className="text-sm text-muted-foreground mb-4">로그인 시 처음 보여질 메인 화면을 선택하세요.</p>
                    <div className="grid grid-cols-3 gap-4">
                      {[
                        { label: '대시보드', value: 'dashboard', desc: '오늘의 요약과 실행 항목' },
                        { label: '이메일', value: 'email', desc: '인박스 중심으로 확인' },
                        { label: '일정 관리', value: 'calendar', desc: '오늘의 회의와 스케줄 확인' }
                      ].map((view) => (
                        <button
                          key={view.value}
                          onClick={() => setWorkspaceStartupView(view.value as 'dashboard' | 'email' | 'calendar')}
                          className={`flex flex-col items-start gap-1 rounded-xl border p-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
                            startupView === view.value
                              ? 'border-primary bg-primary/5 shadow-sm'
                              : 'border-border hover:bg-secondary hover:border-primary/50'
                          }`}
                        >
                          <span className={`font-bold ${startupView === view.value ? 'text-primary' : 'text-foreground'}`}>
                            {view.label}
                          </span>
                          <span className="text-xs text-muted-foreground">{view.desc}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === '연결 계정' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-bold text-xl">이메일 및 캘린더 커넥터</h2>
                    <p className="text-sm text-muted-foreground mt-1">Naruon Relay Proxy를 통해 외부 계정의 데이터를 수집하고 연동합니다.</p>
                  </div>
                  <button className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90">
                    <Plus className="size-4" /> 커넥터 추가
                  </button>
                </div>

                <div className="space-y-4">
                  {/* Connected Accounts */}
                  <div className="rounded-2xl border border-border bg-card p-5 shadow-sm flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="size-10 rounded-full bg-blue-100 grid place-items-center"><Mail className="size-5 text-blue-600" /></div>
                      <div>
                        <h3 className="font-bold text-base">Google Workspace (업무용)</h3>
                        <p className="text-sm text-muted-foreground">seongho@naruon.com • IMAP, SMTP, CalDAV 연동됨</p>
                      </div>
                    </div>
                    <button className="text-sm font-semibold border border-border px-4 py-2 rounded-lg hover:bg-secondary">설정 변경</button>
                  </div>

                  <div className="rounded-2xl border border-border bg-card p-5 shadow-sm flex items-center justify-between opacity-70">
                    <div className="flex items-center gap-4">
                      <div className="size-10 rounded-full bg-slate-100 grid place-items-center"><Mail className="size-5 text-slate-600" /></div>
                      <div>
                        <h3 className="font-bold text-base">개인 메일 (iCloud)</h3>
                        <p className="text-sm text-muted-foreground">seongho.bae@icloud.com • IMAP 수집만 됨 (일정 연동 제외)</p>
                      </div>
                    </div>
                    <button className="text-sm font-semibold border border-border px-4 py-2 rounded-lg hover:bg-secondary">설정 변경</button>
                  </div>
                </div>

                {/* Form Example */}
                <div className="mt-8 rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <h3 className="font-bold text-lg mb-4">IMAP 수동 설정 (사내 메일)</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-bold text-muted-foreground">IMAP 서버 주소</label>
                      <input type="text" placeholder="imap.example.com" className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-bold text-muted-foreground">포트 (SSL)</label>
                      <input type="text" defaultValue="993" className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <label className="text-sm font-bold text-muted-foreground">사용자 계정</label>
                      <input type="email" placeholder="user@company.com" className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                    </div>
                  </div>
                  <button className="mt-6 rounded-lg bg-foreground text-background px-6 py-2 text-sm font-bold hover:bg-foreground/90">연결 테스트</button>
                </div>
              </div>
            )}

            {activeTab === '개발자' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-bold text-xl">개발자 및 시스템 (Observability)</h2>
                    <p className="text-sm text-muted-foreground mt-1">Naruon 인프라 모니터링, 추적 및 보안 로그에 접근합니다.</p>
                  </div>
                </div>

                <section aria-label="Self-hosted connector manifest" className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-bold text-lg">Self-hosted connector manifest</h3>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">
                        Naruon은 이메일 서버가 아닙니다. 고객망의 self-hosted connector가 outbound-only로 naruon.net control plane에 연결해 IMAP/SMTP/CalDAV/WebDAV 접근을 중계합니다.
                      </p>
                    </div>
                    {connectorManifest ? (
                      <span className="rounded-full border border-border bg-background px-3 py-1 font-mono text-xs font-bold text-foreground">
                        {connectorManifest.role}
                      </span>
                    ) : null}
                  </div>

                  {runnerLoading ? (
                    <p className="mt-4 rounded-xl bg-secondary/60 p-3 text-sm font-semibold text-muted-foreground">connector manifest를 불러오는 중입니다.</p>
                  ) : null}
                  {runnerError ? (
                    <p className="mt-4 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm font-semibold text-amber-900">{runnerError}</p>
                  ) : null}
                  {connectorManifest ? (
                    <div className="mt-5 space-y-4">
                      <dl className="grid gap-3 border-t border-border pt-4 sm:grid-cols-3">
                        <div>
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">network_mode</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">{connectorManifest.network_mode}</dd>
                        </div>
                        <div>
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">control_plane_domain</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">{connectorManifest.control_plane_domain}</dd>
                        </div>
                        <div>
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">runner_usage</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">{connectorManifest.runner_usage}</dd>
                        </div>
                      </dl>

                      <div className="grid gap-4 border-t border-border pt-4 md:grid-cols-2">
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">local_protocols</p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {connectorManifest.local_protocols.map((protocol) => (
                              <span key={protocol} className="rounded-full bg-secondary px-2.5 py-1 font-mono text-xs font-semibold text-foreground">{protocol}</span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">prohibited_roles</p>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {connectorManifest.prohibited_roles.map((role) => (
                              <span key={role} className="rounded-full bg-red-50 px-2.5 py-1 font-mono text-xs font-semibold text-red-700">{role}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : null}
                </section>

                <section aria-label="Open-source APM operational signals" className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="flex items-center gap-2 font-bold text-lg">
                        <Activity className="size-5 text-teal-600" />
                        Connector health & APM signals
                      </h3>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">
                        서버가 확인한 self-hosted connector 연결, OpenTelemetry, Prometheus 상태만 표시합니다. Provider write 실행은 여기서 수행하지 않습니다.
                      </p>
                    </div>
                    {operationalSignals ? (
                      <span className="rounded-full border border-border bg-background px-3 py-1 font-mono text-xs font-bold text-foreground">
                        {operationalSignals.audit_event}
                      </span>
                    ) : null}
                  </div>

                  {operationalLoading ? (
                    <p className="mt-4 rounded-xl bg-secondary/60 p-3 text-sm font-semibold text-muted-foreground">운영 신호를 불러오는 중입니다.</p>
                  ) : null}
                  {operationalError ? (
                    <p className="mt-4 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm font-semibold text-amber-900">{operationalError}</p>
                  ) : null}
                  {operationalSignals ? (
                    <div className="mt-5 space-y-5">
                      <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        <div className="rounded-xl border border-border bg-background p-3">
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">connection_state</dt>
                          <dd className="mt-1 font-mono text-sm font-bold text-foreground">{operationalSignals.connector.connection_state}</dd>
                        </div>
                        <div className="rounded-xl border border-border bg-background p-3">
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">active_connections</dt>
                          <dd className="mt-1 font-mono text-sm font-bold text-foreground">{operationalSignals.connector.active_connection_count}</dd>
                        </div>
                        <div className="rounded-xl border border-border bg-background p-3">
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">prometheus</dt>
                          <dd className="mt-1 font-mono text-sm font-bold text-foreground">{operationalSignals.telemetry.prometheus_metrics_enabled ? 'enabled' : 'not_configured'}</dd>
                        </div>
                        <div className="rounded-xl border border-border bg-background p-3">
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">otel_traces</dt>
                          <dd className="mt-1 font-mono text-sm font-bold text-foreground">{operationalSignals.telemetry.otel_traces_enabled ? 'enabled' : 'not_configured'}</dd>
                        </div>
                      </dl>

                      <dl className="grid gap-3 border-t border-border pt-4 sm:grid-cols-3">
                        <div>
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">last_heartbeat_at</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">{operationalSignals.connector.last_heartbeat_at ?? 'none'}</dd>
                        </div>
                        <div>
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">last_disconnect_at</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">{operationalSignals.connector.last_disconnect_at ?? 'none'}</dd>
                        </div>
                        <div>
                          <dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">otel_endpoint_host</dt>
                          <dd className="mt-1 font-mono text-sm text-foreground">{operationalSignals.telemetry.otel_endpoint_host ?? 'none'}</dd>
                        </div>
                      </dl>

                      <div aria-labelledby="recent-connector-signals-heading" className="border-t border-border pt-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <h4 id="recent-connector-signals-heading" className="font-bold text-sm">Recent connector signals</h4>
                          <span className="rounded-full bg-secondary px-2.5 py-1 font-mono text-xs font-semibold text-foreground">{connectorEvents.length} events</span>
                        </div>
                        {connectorEvents.length > 0 ? (
                          <ol className="mt-3 divide-y divide-border">
                            {connectorEvents.map((event) => (
                              <li key={event.event_uid} className="grid gap-2 py-3 sm:grid-cols-[minmax(0,1fr)_auto]">
                                <div className="min-w-0">
                                  <p className="font-mono text-xs font-bold text-foreground">{event.state_code}</p>
                                  <p className="mt-1 break-words text-sm leading-6 text-muted-foreground">{event.detail_text ?? event.signal_key}</p>
                                  <p className="mt-1 break-all font-mono text-[11px] text-muted-foreground">{event.event_uid}</p>
                                </div>
                                <time className="break-all font-mono text-xs text-muted-foreground sm:text-right">{event.observed_at}</time>
                              </li>
                            ))}
                          </ol>
                        ) : (
                          <p className="mt-3 text-sm leading-6 text-muted-foreground">Durable connector history has not recorded a runner event yet.</p>
                        )}
                      </div>

                      <div className="grid gap-3 md:grid-cols-2">
                        {operationalSignals.signals.map((signal) => (
                          <article key={signal.signal_key} className="rounded-xl border border-border bg-background p-4">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <h4 className="font-bold text-sm">{signal.display_name}</h4>
                              <span className="rounded-full bg-secondary px-2.5 py-1 font-mono text-xs font-semibold text-foreground">{signal.state}</span>
                            </div>
                            <p className="mt-2 text-sm leading-6 text-muted-foreground">{signal.detail}</p>
                            <p className="mt-3 break-all font-mono text-xs text-muted-foreground">{signal.evidence_source}</p>
                          </article>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </section>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                  <a href="http://localhost:3000" target="_blank" rel="noreferrer" className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-6 shadow-sm hover:border-primary/50 transition-colors">
                    <Monitor className="size-8 text-orange-500 mb-2" />
                    <h3 className="font-bold text-lg">Grafana 대시보드</h3>
                    <p className="text-sm text-muted-foreground">OpenTelemetry 기반의 APM, 트래픽 메트릭 및 시스템 자원 모니터링을 확인합니다.</p>
                  </a>
                  <a href="http://localhost:8080" target="_blank" rel="noreferrer" className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-6 shadow-sm hover:border-primary/50 transition-colors">
                    <Shield className="size-8 text-blue-500 mb-2" />
                    <h3 className="font-bold text-lg">Keycloak 관리 콘솔</h3>
                    <p className="text-sm text-muted-foreground">OIDC 프로바이더, SSO 인증, 역할 기반 접근 제어(RBAC)를 구성합니다.</p>
                  </a>
                  <a href="http://localhost:3100" target="_blank" rel="noreferrer" className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-6 shadow-sm hover:border-primary/50 transition-colors">
                    <AlertCircle className="size-8 text-slate-500 mb-2" />
                    <h3 className="font-bold text-lg">Loki 로그 서버</h3>
                    <p className="text-sm text-muted-foreground">분산 아키텍처 환경의 컨테이너 로그 및 어플리케이션 에러 로그를 검색합니다.</p>
                  </a>
                  <a href="http://localhost:3200" target="_blank" rel="noreferrer" className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-6 shadow-sm hover:border-primary/50 transition-colors">
                    <RefreshCw className="size-8 text-teal-500 mb-2" />
                    <h3 className="font-bold text-lg">Tempo 분산 추적</h3>
                    <p className="text-sm text-muted-foreground">FastAPI의 엔드포인트 지연율 및 MSA 구성요소 간의 호출 트레이스를 시각화합니다.</p>
                  </a>
                </div>
              </div>
            )}

            {detailSurface ? (
              <section aria-label={`${activeTab} 상세 설정`} className="space-y-5">
                <div>
                  <h2 className="font-bold text-xl">{detailSurface.heading}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{detailSurface.copy}</p>
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  {detailSurface.items.map((item) => (
                    <article key={item.title} className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                      <p className="rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary inline-flex">{item.status}</p>
                      <h3 className="mt-4 font-bold text-base">{item.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.detail}</p>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}
            
          </div>
        </main>
      </div>
    </div>
  );
}
