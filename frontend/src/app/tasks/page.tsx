import Link from 'next/link';
import { CheckCircle2, Inbox, ListChecks, ShieldCheck } from 'lucide-react';

const taskStates = [
  { title: 'Open', copy: '메일과 일정에서 추출된 실행 항목이 티켓처럼 접수됩니다.' },
  { title: 'In progress', copy: '담당자, 마감, 관련 스레드, 차단 사유를 추적합니다.' },
  { title: 'Blocked', copy: '외부 답장, 일정 충돌, 권한 거부처럼 해결 전제가 필요한 항목입니다.' },
  { title: 'Done', copy: '완료 후에도 원본 이메일과 writeback 감사 흔적을 유지합니다.' },
];

export default function TasksPage() {
  return (
    <div className="h-full min-h-0 overflow-y-auto bg-gradient-to-br from-primary/5 via-background to-emerald-500/5 p-4 sm:p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="rounded-3xl border border-primary/15 bg-card/95 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">Ticket tasks</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-foreground">할 일 추적</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            메일에서 도출된 메모, Todo, 일정 후보를 티켓형 업무로 바꿉니다. 각 업무는 원본 메일, 스레드, 담당자, 상태, 차단 사유와 연결됩니다.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/" className="inline-flex min-h-11 items-center gap-2 rounded-2xl bg-primary px-4 text-sm font-bold text-primary-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
              <Inbox className="size-4" aria-hidden="true" />
              메일에서 할 일 만들기
            </Link>
            <Link href="/calendar" className="inline-flex min-h-11 items-center gap-2 rounded-2xl border border-border bg-card px-4 text-sm font-bold text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
              일정 후보 확인
            </Link>
          </div>
        </section>

        <section aria-label="할 일 상태 보드" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {taskStates.map(({ title, copy }) => (
            <article key={title} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-2xl bg-primary/10 text-primary">
                  <ListChecks className="size-5" aria-hidden="true" />
                </span>
                <h2 className="text-lg font-black text-foreground">{title}</h2>
              </div>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">{copy}</p>
            </article>
          ))}
        </section>

        <section aria-label="데이터 주권 원칙" className="rounded-3xl border border-border bg-card/90 p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="grid size-11 place-items-center rounded-2xl bg-emerald-500/10 text-emerald-700">
              <ShieldCheck className="size-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-xl font-black text-foreground">원본 시스템 추적</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Naruon에만 저장되는 고립된 할 일은 만들지 않습니다. 새 업무는 원본 메일/스레드와 연결되고, 일정/파일 writeback은 고객 소유 계정의 CalDAV/WebDAV 원본으로 돌아갑니다.
              </p>
            </div>
          </div>
          <div className="mt-5 rounded-2xl border border-border bg-background/70 p-4 text-sm font-semibold text-foreground">
            <CheckCircle2 className="mr-2 inline size-4 text-emerald-600" aria-hidden="true" />
            다음 구현 단계: 담당자 배정, 상태 전환 감사 로그, 중복 업무 병합, 원본 이메일 상황 변화 추적.
          </div>
        </section>
      </div>
    </div>
  );
}
