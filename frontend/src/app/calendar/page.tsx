import Link from 'next/link';
import { CalendarDays, CheckCircle2, GitBranch, RefreshCw, ShieldCheck, Users } from 'lucide-react';

const calendarFlows = [
  'IMAP/OAuth 계정별 메일에서 일정 후보를 추출합니다.',
  '각 계정의 CalDAV 원본, ETag, sync token, write 권한을 확인합니다.',
  '충돌이 있으면 Naruon 내부 저장으로 숨기지 않고 해결 상태를 노출합니다.',
  '사용자 승인 후 원본 계정 writeback intent와 감사 이벤트를 준비합니다.',
];

const calendarScreens = [
  { title: '월간 캘린더', detail: '원본 계정별 색상, 반복 일정, 휴가·회의·마감 밀도를 한 달 단위로 봅니다.' },
  { title: '주간 캘린더', detail: '이번 주 회의 조율, 이동 시간, 마감 충돌을 시간대별로 검증합니다.' },
  { title: '일정 상세', detail: '참석자, 원본 CalDAV UID, ETag, 관련 메일 스레드, writeback 상태를 함께 보여줍니다.' },
  { title: '회의 조율', detail: '메일에서 추출한 후보 시간과 참석자 availability를 비교해 승인 전 상태로 둡니다.' },
  { title: '일정 후보', detail: '개인 메일에 도착한 회사 회의도 주제·참석자·프로젝트로 가장 타당한 회사 계정에 배정합니다.' },
];

const caldavQueues = [
  { account: '회사 CalDAV', item: '파트너 미팅 일정 확정', target: 'company-calendar/projects/q2-launch.ics', status: 'ETag 확인 후 writeback intent 대기' },
  { account: '개인 CalDAV', item: '가족 일정과 업무 회의 분리', target: 'personal-calendar/private.ics', status: '업무성 낮음, 개인 계정 유지' },
  { account: 'Naruon CalDAV', item: '조직화된 통합 일정 보기', target: 'naruon.net/dav/calendar/organized', status: '원본별 provenance 포함' },
];

export default function CalendarPage() {
  return (
    <div className="h-full min-h-0 overflow-y-auto bg-gradient-to-br from-primary/5 via-background to-card p-4 sm:p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="rounded-3xl border border-primary/15 bg-card/95 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">CalDAV workspace</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-foreground">일정 관리</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            여러 메일/캘린더 계정에서 흩어진 회의, 마감, 할 일을 읽고 고객 소유 CalDAV 원본으로 되돌릴 후보와 intent를 정리합니다.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/#mobile-calendar" className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-primary px-4 text-sm font-bold text-primary-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
              <CalendarDays className="size-4" aria-hidden="true" />
              모바일 일정 후보 열기
            </Link>
            <Link href="/settings" className="inline-flex min-h-11 items-center gap-2 rounded-2xl border border-border bg-card px-4 text-sm font-bold text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
              커넥터 설정
            </Link>
          </div>
        </section>

        <section aria-label="CalDAV writeback flow" className="rounded-3xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="grid size-11 place-items-center rounded-2xl bg-primary/10 text-primary">
              <GitBranch className="size-5" aria-hidden="true" />
            </span>
            <h2 className="text-xl font-black text-foreground">원본 계정 writeback 흐름</h2>
          </div>
          <ol className="mt-5 grid gap-3 md:grid-cols-2">
            {calendarFlows.map((flow, index) => (
              <li key={flow} className="rounded-2xl border border-border bg-background/70 p-4 text-sm leading-6 text-foreground">
                <span className="mr-2 inline-flex size-6 items-center justify-center rounded-full bg-primary text-xs font-black text-primary-foreground">{index + 1}</span>
                {flow}
              </li>
            ))}
          </ol>
        </section>

        <section aria-label="일정 화면 구성" className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {calendarScreens.map(({ title, detail }) => (
            <article key={title} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
              <CalendarDays className="size-5 text-primary" aria-hidden="true" />
              <h2 className="mt-3 text-lg font-black text-foreground">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{detail}</p>
            </article>
          ))}
        </section>

        <section aria-label="CalDAV 계정별 writeback 큐" className="rounded-3xl border border-border bg-card/90 p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="grid size-11 place-items-center rounded-2xl bg-primary/10 text-primary"><Users className="size-5" aria-hidden="true" /></span>
            <div>
              <h2 className="text-xl font-black text-foreground">CalDAV 계정별 writeback 큐</h2>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">Naruon에만 저장하지 않고 원본 계정의 권한, ETag, provenance를 확인한 뒤 writeback intent를 준비합니다.</p>
            </div>
          </div>
          <div className="mt-5 grid gap-3">
            {caldavQueues.map(({ account, item, target, status }) => (
              <article key={`${account}-${item}`} className="rounded-2xl border border-border bg-background/75 p-4 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-black text-foreground">{account}</h3>
                  <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">{status}</span>
                </div>
                <p className="mt-2 font-semibold text-foreground">{item}</p>
                <p className="mt-1 text-xs text-muted-foreground">대상: {target}</p>
              </article>
            ))}
          </div>
        </section>

        <section aria-label="일정 충돌 상태" className="grid gap-4 md:grid-cols-2">
          <article className="rounded-3xl border border-border bg-card p-5 shadow-sm">
            <RefreshCw className="size-5 text-primary" aria-hidden="true" />
            <h2 className="mt-3 text-lg font-black text-foreground">동기화 상태</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">커넥터 heartbeat, sync lag, provider rate limit, writeback conflict 후보를 APM 대시보드에 연결합니다.</p>
          </article>
          <article className="rounded-3xl border border-border bg-card p-5 shadow-sm">
            <ShieldCheck className="size-5 text-emerald-700" aria-hidden="true" />
            <h2 className="mt-3 text-lg font-black text-foreground">데이터 주권</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">Naruon 로컬 캐시는 검색과 AI 맥락용입니다. 조직화된 결과는 고객 원본 계정에 조건부 writeback intent로 남깁니다.</p>
          </article>
          <article className="rounded-3xl border border-border bg-card p-5 shadow-sm">
            <CheckCircle2 className="size-5 text-emerald-700" aria-hidden="true" />
            <h2 className="mt-3 text-lg font-black text-foreground">승인 전 검증</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">AI가 정리한 일정도 사용자가 계정과 대상 캘린더를 확인하기 전에는 원본 기록 후보로만 유지합니다.</p>
          </article>
        </section>
      </div>
    </div>
  );
}
