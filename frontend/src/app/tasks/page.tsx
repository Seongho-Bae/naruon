'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { CheckCircle2, Inbox, ListChecks, ShieldCheck, UserRoundCheck } from 'lucide-react';

import { apiClient } from '@/lib/api-client';

type TaskStatus = 'open' | 'in_progress' | 'blocked' | 'done';
type TaskPriority = 'low' | 'normal' | 'high' | 'urgent';

interface TicketTask {
  id: string;
  title: string;
  status: TaskStatus;
  priority: TaskPriority;
  source_type: string;
  source_email_id: string | null;
  related_thread_id: string | null;
  created_at: string;
  updated_at: string;
}

const taskStates = [
  { title: '접수', copy: '메일과 일정에서 추출된 실행 항목이 원본 메일 링크와 함께 티켓처럼 들어옵니다.' },
  { title: '진행', copy: '담당자, 마감, 관련 스레드, 차단 사유를 한 카드에서 추적합니다.' },
  { title: '차단', copy: '외부 답장, 일정 충돌, 권한 거부처럼 해결 전제가 필요한 항목을 분리합니다.' },
  { title: '완료', copy: '완료 후에도 원본 이메일, 답변 추적, writeback intent 감사 흔적을 유지합니다.' },
];

const taskViews = [
  { title: '내 작업', copy: '오늘 내가 처리해야 하는 답장, 일정 조율, 문서 검토를 우선순위로 정렬합니다.' },
  { title: '위임한 작업', copy: '다른 담당자에게 넘긴 항목의 응답 지연과 차단 사유를 추적합니다.' },
  { title: '칸반', copy: '접수, 진행, 차단, 완료 열로 업무 흐름을 옮기며 상태 변경 이력을 남깁니다.' },
  { title: '작업 상세', copy: '원본 메일, 관련 스레드, 담당자, 답변 추적 상태, 일정 후보를 한 화면에 둡니다.' },
];

const sourceLinkedTasks = [
  { title: '원본 메일', detail: 'Message-ID, thread public id, 발신자 DAG를 보존해 업무 출처를 잃지 않습니다.' },
  { title: '답변 추적', detail: '보낸 메일의 회신 여부와 SLA를 작업 상태에 연결해 후속 알림을 만듭니다.' },
];

const statusLabels: Record<TaskStatus, string> = {
  open: '접수',
  in_progress: '진행',
  blocked: '차단',
  done: '완료',
};

const priorityLabels: Record<TaskPriority, string> = {
  low: '낮음',
  normal: '보통',
  high: '높음',
  urgent: '긴급',
};

function sourceLabel(task: TicketTask) {
  if (task.source_email_id) return task.source_email_id;
  return task.source_type === 'email' ? '메일 출처 확인 중' : task.source_type;
}

export default function TasksPage() {
  const [tickets, setTickets] = useState<TicketTask[]>([]);
  const [taskLoadState, setTaskLoadState] = useState<'loading' | 'ready' | 'error'>('loading');

  const loadTickets = useCallback(async () => {
    try {
      const data = await apiClient.get<TicketTask[]>('/api/tasks');
      setTickets(data);
      setTaskLoadState('ready');
    } catch {
      setTickets([]);
      setTaskLoadState('error');
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(loadTickets);
  }, [loadTickets]);

  return (
    <div className="h-full min-h-0 overflow-y-auto bg-gradient-to-br from-primary/5 via-background to-emerald-500/5 p-4 sm:p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="rounded-3xl border border-primary/15 bg-card/95 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-primary">Source-linked tasks</p>
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

        <section aria-label="작업 화면" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {taskViews.map(({ title, copy }) => (
            <article key={title} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
              <UserRoundCheck className="size-5 text-primary" aria-hidden="true" />
              <h2 className="mt-3 text-lg font-black text-foreground">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy}</p>
            </article>
          ))}
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

        <section aria-label="소스 연결 티켓 보드" className="rounded-3xl border border-border bg-card/90 p-6 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-primary">Live task board</p>
              <h2 className="mt-2 text-xl font-black text-foreground">원본 메일 기반 티켓</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                백엔드 `/api/tasks`의 tenant-scoped 응답을 signed session으로 읽어 원본 메일, 스레드, 상태, 우선순위를 같은 카드에서 추적합니다.
              </p>
            </div>
            <Link href="/mail" className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl border border-border bg-background px-4 text-sm font-bold text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
              메일 작업공간 열기
            </Link>
          </div>

          {taskLoadState === 'loading' ? (
            <div role="status" aria-live="polite" className="mt-5 rounded-2xl border border-dashed border-border bg-background/70 p-4 text-sm font-bold text-muted-foreground">
              원본 메일 기반 할 일을 불러오는 중입니다.
            </div>
          ) : null}

          {taskLoadState === 'error' ? (
            <div role="alert" className="mt-5 rounded-2xl border border-destructive/30 bg-destructive/10 p-4 text-sm font-bold text-destructive">
              할 일 목록을 불러오지 못했습니다. 인증된 워크스페이스 세션을 확인한 뒤 다시 시도하세요.
              <button type="button" onClick={() => { setTaskLoadState('loading'); void loadTickets(); }} className="mt-3 inline-flex min-h-10 items-center rounded-xl border border-destructive/30 bg-card px-3 text-sm font-bold text-destructive focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
                다시 불러오기
              </button>
            </div>
          ) : null}

          {taskLoadState === 'ready' && tickets.length === 0 ? (
            <div className="mt-5 rounded-2xl border border-dashed border-border bg-background/70 p-4 text-sm leading-6 text-muted-foreground">
              아직 생성된 티켓형 할 일이 없습니다. 메일 상세의 `할 일 만들기`에서 실행 항목을 원본 스레드와 연결하세요.
            </div>
          ) : null}

          {taskLoadState === 'ready' && tickets.length > 0 ? (
            <div className="mt-5 grid gap-4 lg:grid-cols-2">
              {tickets.map((task) => (
                <article key={task.id} className="rounded-2xl border border-border bg-background/80 p-4 shadow-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-black text-primary">{statusLabels[task.status]}</span>
                    <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-black text-emerald-700">{priorityLabels[task.priority]}</span>
                  </div>
                  <h3 className="mt-3 text-lg font-black text-foreground">{task.title}</h3>
                  <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                    <div className="rounded-2xl border border-border bg-card p-3">
                      <dt className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">원본 메일</dt>
                      <dd className="mt-1 break-words font-semibold text-foreground">{sourceLabel(task)}</dd>
                    </div>
                    <div className="rounded-2xl border border-border bg-card p-3">
                      <dt className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">관련 스레드</dt>
                      <dd className="mt-1 break-words font-semibold text-foreground">{task.related_thread_id ?? '스레드 연결 대기'}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          ) : null}
        </section>

        <section aria-label="원본 메일과 답변 추적" className="grid gap-4 md:grid-cols-2">
          {sourceLinkedTasks.map(({ title, detail }) => (
            <article key={title} className="rounded-3xl border border-border bg-card p-5 shadow-sm">
              <CheckCircle2 className="size-5 text-emerald-700" aria-hidden="true" />
              <h2 className="mt-3 text-lg font-black text-foreground">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{detail}</p>
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
                Naruon에만 저장되는 고립된 할 일은 만들지 않습니다. 새 업무는 원본 메일/스레드와 연결되고, 일정/파일 writeback은 고객 소유 계정의 CalDAV/WebDAV 원본 후보와 provenance를 남깁니다.
              </p>
            </div>
          </div>
          <div className="mt-5 rounded-2xl border border-border bg-background/70 p-4 text-sm font-semibold text-foreground">
            <CheckCircle2 className="mr-2 inline size-4 text-emerald-600" aria-hidden="true" />
            담당자 배정, 상태 전환 감사 로그, 중복 업무 병합, 원본 이메일 상황 변화 추적이 활성화됩니다.
          </div>
        </section>
      </div>
    </div>
  );
}
