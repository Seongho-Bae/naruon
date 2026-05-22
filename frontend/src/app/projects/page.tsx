import Link from 'next/link';
import { CalendarDays, CheckCircle2, FolderOpen, LockKeyhole, Mail, Network, ServerCog, ShieldCheck } from 'lucide-react';

const projectSections = [
  {
    id: 'launch',
    title: '런칭 프로젝트',
    description: '출시 메일, 일정, 첨부파일, 의사결정을 하나의 실행 보드로 묶습니다.',
    bullets: ['메일 thread와 중복 반입 정리', 'CalDAV 일정 writeback 후보', 'WebDAV 산출물 폴더 매핑'],
  },
  {
    id: 'vendor',
    title: '벤더 관리',
    description: '계약, 보안 검토, 운영 이슈를 계정별 데이터 주권을 유지하며 추적합니다.',
    bullets: ['RBAC/ABAC deny 우선 정책', 'Keycloak/Casdoor 기업 로그인', 'Traefik 경계 라우팅'],
  },
  {
    id: 'marketing',
    title: '마케팅 캠페인',
    description: '캠페인 메일, 연락처, 일정, 리포트 초안을 후속 업무로 연결합니다.',
    bullets: ['CardDAV 관계 맥락', 'OpenTelemetry 실행 추적', 'PR 자동 거버넌스 피드백'],
  },
];

const projectDetailCards = [
  { title: '의사결정 로그', copy: '메일, 회의, 파일에서 결정 근거와 승인자를 추출해 프로젝트별 변경 이력으로 남깁니다.' },
  { title: '일정·작업 연결', copy: 'CalDAV 일정 후보와 티켓 작업을 프로젝트 milestone에 연결하고 차단 사유를 노출합니다.' },
  { title: '산출물 provenance', copy: 'WebDAV 파일, AI 요약, 공유 링크가 어느 원본 thread와 계정에서 왔는지 추적합니다.' },
];

const architectureCards = [
  { title: '외부 메일 relay/proxy', icon: Mail, copy: 'Naruon은 이메일 서버가 아니라 사용자가 지정한 IMAP/POP3/SMTP/OAuth 공급자에 접속하는 웹 클라이언트 서버입니다.' },
  { title: 'self-hosted connector', icon: ServerCog, copy: '사내망 전용 메일 서버는 고객 네트워크의 outbound-only connector가 naruon.net control plane과 통신합니다.' },
  { title: 'CalDAV/CardDAV/WebDAV', icon: CalendarDays, copy: '계정 N개의 일정·연락처·파일을 읽고, ETag/If-Match 충돌 방지와 provenance로 원본 계정 writeback intent를 준비합니다.' },
  { title: 'RBAC/ABAC', icon: ShieldCheck, copy: 'SaaS 관리자, 기업/그룹/사업부/팀, 개인/SOHO를 universal tenant model로 다루고 ABAC deny가 RBAC allow보다 우선합니다.' },
  { title: 'Keycloak/Casdoor + Traefik', icon: LockKeyhole, copy: 'OIDC, enterprise federation, ForwardAuth, route policy, rate limit을 edge에서 분리해 자체 로그인과 외부 SSO를 함께 지원합니다.' },
  { title: 'OpenTelemetry APM', icon: Network, copy: 'Prometheus, Loki, Tempo/Jaeger, Grafana로 connector heartbeat, sync lag, writeback conflict, AI action audit trail을 봅니다.' },
];

export default function ProjectsPage() {
  return (
    <div className="min-h-full overflow-y-auto bg-gradient-to-br from-primary/5 via-background to-emerald-500/5 p-4 sm:p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="rounded-3xl border border-primary/15 bg-card/95 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">Project workspace</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-foreground">프로젝트 워크스페이스</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            브랜딩 시안의 받은편지함, 일정 연결, 파일, 관계 맥락, 보고서 초안을 프로젝트 단위로 묶어 실행 가능한 메뉴 구조로 정리합니다.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/#mobile-calendar" className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-primary px-4 text-sm font-bold text-primary-foreground shadow-[0_16px_34px_rgba(37,99,255,0.24)] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
              <CalendarDays className="size-4" aria-hidden="true" />
              일정 후보 열기
            </Link>
            <Link href="/ai-hub#actions" className="inline-flex min-h-11 items-center gap-2 rounded-2xl border border-border bg-background px-4 text-sm font-bold text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
              <CheckCircle2 className="size-4 text-primary" aria-hidden="true" />
              실행 항목 보기
            </Link>
          </div>
        </section>

        <div className="grid gap-4 lg:grid-cols-3">
          {projectSections.map((section) => (
            <section key={section.id} id={section.id} aria-label={section.title} className="scroll-mt-24 rounded-3xl border border-border bg-card p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-2xl bg-primary/10 text-primary"><FolderOpen className="size-5" aria-hidden="true" /></span>
                <h2 className="text-lg font-black text-foreground">{section.title}</h2>
              </div>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">{section.description}</p>
              <ul className="mt-4 space-y-2 text-sm text-foreground">
                {section.bullets.map((bullet, index) => (
                  <li key={index} className="flex gap-2 rounded-2xl border border-border bg-background/70 px-3 py-2">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600" aria-hidden="true" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        <section aria-label="프로젝트 상세 작업" className="grid gap-4 md:grid-cols-3">
          {projectDetailCards.map(({ title, copy }) => (
            <article key={title} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
              <CheckCircle2 className="size-5 text-primary" aria-hidden="true" />
              <h2 className="mt-3 text-lg font-black text-foreground">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy}</p>
            </article>
          ))}
        </section>

        <section aria-label="북극성 통합 설계" className="rounded-3xl border border-border bg-card/90 p-6 shadow-sm">
          <h2 className="text-xl font-black text-foreground">북극성 통합 설계</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {architectureCards.map(({ title, icon: Icon, copy }) => (
              <article key={title} className="rounded-3xl border border-border bg-background/75 p-4 shadow-sm">
                <div className="flex items-center gap-3">
                  <span className="grid size-10 place-items-center rounded-2xl bg-primary/10 text-primary"><Icon className="size-5" aria-hidden="true" /></span>
                  <h3 className="font-black text-foreground">{title}</h3>
                </div>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{copy}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
