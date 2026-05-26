"use client";

import { useEffect, useMemo, useState } from 'react';
import { Plus, Search, Filter, MoreHorizontal, User, CalendarDays, Inbox, AlertCircle } from 'lucide-react';

import { apiClient } from '@/lib/api-client';

const MOCK_TASKS = {
  open: [
    { id: 'T-101', title: '고객사 A 제안서 검토', tags: ['우선순위 높음', '제안'], due: '오늘 마감', assignee: '김나루', source: 'Inbox', priority: 'high', status: 'open' },
    { id: 'T-102', title: '디자인 시스템 업데이트 리뷰', tags: ['디자인', '리뷰'], due: '내일 마감', assignee: '김나루', source: 'Design Thread', priority: 'normal', status: 'open' },
  ],
  in_progress: [
    { id: 'T-103', title: 'Q2 리스크 점검 회의록 작성', tags: ['회의록', '리스크'], due: '5/27 마감', assignee: '김나루', source: 'Meeting', priority: 'normal', status: 'in_progress' },
  ],
  blocked: [
    { id: 'T-104', title: '외부 API 연동 권한 승인 대기', tags: ['권한', '개발'], due: '기한 없음', assignee: '박지현', source: 'IT Support', priority: 'urgent', status: 'blocked' },
  ],
  done: [
    { id: 'T-105', title: '주간 파트 미팅 준비', tags: ['미팅'], due: '완료됨', assignee: '김나루', source: 'Calendar', priority: 'low', status: 'done' },
  ],
};

type TicketTask = {
  id: string;
  title: string;
  status: 'open' | 'in_progress' | 'blocked' | 'done';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  source_type: string;
  source_email_id: string | null;
  related_thread_id: string | null;
  updated_at: string;
};

const taskStatusLabels: Record<TicketTask['status'], string> = {
  open: '접수',
  in_progress: '진행',
  blocked: '차단',
  done: '완료',
};

const taskPriorityLabels: Record<TicketTask['priority'], string> = {
  low: '낮음',
  normal: '보통',
  high: '높음',
  urgent: '긴급',
};

export function TasksLayout() {
  const [viewMode, setViewMode] = useState<'내 작업' | '위임한 작업' | '칸반' | '작업 상세'>('칸반');
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [tasks, setTasks] = useState(MOCK_TASKS);
  const [draggedTask, setDraggedTask] = useState<{id: string, sourceCol: string} | null>(null);
  const [ticketTasks, setTicketTasks] = useState<TicketTask[]>([]);
  const [ticketStatus, setTicketStatus] = useState<'loading' | 'ready' | 'empty' | 'error'>('loading');

  useEffect(() => {
    let cancelled = false;

    void apiClient
      .get<TicketTask[]>('/api/tasks')
      .then((apiTasks) => {
        if (cancelled) return;
        setTicketTasks(apiTasks);
        setTicketStatus(apiTasks.length > 0 ? 'ready' : 'empty');
      })
      .catch(() => {
        if (cancelled) return;
        setTicketTasks([]);
        setTicketStatus('error');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const handleDragStart = (e: React.DragEvent, id: string, sourceCol: string) => {
    setDraggedTask({ id, sourceCol });
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetCol: keyof typeof MOCK_TASKS) => {
    e.preventDefault();
    if (!draggedTask) return;
    if (draggedTask.sourceCol === targetCol) return;

    setTasks(prev => {
      const sourceList = [...prev[draggedTask.sourceCol as keyof typeof MOCK_TASKS]];
      const targetList = [...prev[targetCol]];
      const taskIndex = sourceList.findIndex(t => t.id === draggedTask.id);
      if (taskIndex === -1) return prev;
      
      const [movedTask] = sourceList.splice(taskIndex, 1);
      targetList.push({ ...movedTask, status: targetCol });

      return {
        ...prev,
        [draggedTask.sourceCol]: sourceList,
        [targetCol]: targetList,
      };
    });
    setDraggedTask(null);
  };

  const currentColumns = [
    { id: 'open', title: '접수', count: tasks.open.length, color: 'bg-blue-100 text-blue-700' },
    { id: 'in_progress', title: '진행', count: tasks.in_progress.length, color: 'bg-orange-100 text-orange-700' },
    { id: 'blocked', title: '차단', count: tasks.blocked.length, color: 'bg-red-100 text-red-700' },
    { id: 'done', title: '완료', count: tasks.done.length, color: 'bg-green-100 text-green-700' },
  ];

  const liveBoardCounts = useMemo(() => {
    return ticketTasks.reduce<Record<TicketTask['status'], number>>(
      (acc, task) => {
        acc[task.status] += 1;
        return acc;
      },
      { open: 0, in_progress: 0, blocked: 0, done: 0 },
    );
  }, [ticketTasks]);

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground flex-col">
      {/* Top Header */}
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-border px-6 bg-card">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold">할 일 추적</h1>
          <p className="sr-only">리소스 배정 검토 회의</p>
          <div className="flex overflow-hidden rounded-md border border-border">
            {['내 작업', '위임한 작업', '칸반', '작업 상세'].map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode as '내 작업' | '위임한 작업' | '칸반' | '작업 상세')}
                className={`px-4 py-1.5 text-sm font-semibold transition-colors ${viewMode === mode ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-secondary'}`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <input type="text" placeholder="작업 검색..." className="h-9 w-64 rounded-md border border-border bg-background pl-9 pr-4 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary" />
          </div>
          <button className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-1.5 text-sm font-semibold hover:bg-secondary">
            <Filter className="size-4" /> 필터
          </button>
          <button className="flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-bold text-primary-foreground hover:bg-primary/90">
            <Plus className="size-4" /> 새 작업
          </button>
        </div>
      </header>

      {/* Kanban Board Area */}
      <main className="flex-1 overflow-x-auto overflow-y-auto p-6 bg-secondary/20">
        <section aria-label="API 연결 작업" className="mb-6 rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-bold">실제 티켓 큐</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                `/api/tasks`에서 원본 메일, 스레드, 상태와 우선순위를 읽어 티켓 보드와 함께 추적합니다.
              </p>
            </div>
            <div role="status" aria-live="polite" className="rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
              {ticketStatus === 'loading' ? '작업 불러오는 중' : null}
              {ticketStatus === 'ready' ? `${ticketTasks.length}개 티켓 연결` : null}
              {ticketStatus === 'empty' ? '연결된 티켓 없음' : null}
              {ticketStatus === 'error' ? '인증된 세션 필요' : null}
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-4">
            {(Object.keys(taskStatusLabels) as TicketTask['status'][]).map((status) => (
              <div key={status} className="rounded-lg border border-border bg-background/70 p-3">
                <p className="text-xs font-bold text-muted-foreground">{taskStatusLabels[status]}</p>
                <p className="mt-1 text-xl font-bold text-foreground">{liveBoardCounts[status]}</p>
              </div>
            ))}
          </div>

          {ticketStatus === 'ready' ? (
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {ticketTasks.slice(0, 4).map((task) => (
                <article key={task.id} className="rounded-lg border border-border bg-background/75 p-3 text-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-bold text-foreground">{task.title}</h3>
                    <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-bold text-primary">
                      {taskStatusLabels[task.status]} · {taskPriorityLabels[task.priority]}
                    </span>
                  </div>
                  <dl className="mt-2 grid gap-2 text-xs text-muted-foreground sm:grid-cols-3">
                    <div>
                      <dt className="font-bold text-foreground">원본</dt>
                      <dd>{task.source_email_id ?? task.source_type}</dd>
                    </div>
                    <div>
                      <dt className="font-bold text-foreground">스레드</dt>
                      <dd>{task.related_thread_id ?? '비공개'}</dd>
                    </div>
                    <div>
                      <dt className="font-bold text-foreground">업데이트</dt>
                      <dd suppressHydrationWarning>{new Date(task.updated_at).toLocaleString('ko-KR')}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          ) : null}

          {ticketStatus === 'empty' ? (
            <p className="mt-4 rounded-lg border border-dashed border-border bg-background/70 p-3 text-sm text-muted-foreground">
              메일 상세에서 실행 항목을 만들면 source-linked 티켓으로 표시됩니다.
            </p>
          ) : null}

          {ticketStatus === 'error' ? (
            <p className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
              작업 API는 signed session이 있을 때만 읽습니다. 공개 identity header는 사용하지 않습니다.
            </p>
          ) : null}
        </section>

        {viewMode === '칸반' && (
          <div className="flex min-h-[560px] gap-6">
            {currentColumns.map((col) => (
              <div
                key={col.id}
                className="flex h-full w-80 flex-col rounded-xl bg-card border border-border shadow-sm shrink-0"
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, col.id as keyof typeof MOCK_TASKS)}
              >
                <div className="flex items-center justify-between border-b border-border p-4">
                  <div className="flex items-center gap-2">
                    <h2 className="font-bold text-sm">{col.title}</h2>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${col.color}`}>{col.count}</span>
                  </div>
                  <button className="text-muted-foreground hover:text-foreground"><MoreHorizontal className="size-4" /></button>
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                  {tasks[col.id as keyof typeof MOCK_TASKS].map((task) => (
                    <div
                      key={task.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, task.id, col.id)}
                      className="cursor-grab active:cursor-grabbing rounded-lg border border-border bg-background p-3 shadow-sm hover:border-primary/50 hover:shadow-md transition-all"
                    >
                      <div className="flex flex-wrap gap-1 mb-2">
                        {task.tags.map((tag) => (
                          <span key={tag} className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-bold text-secondary-foreground">{tag}</span>
                        ))}
                      </div>
                      <h3 className="font-bold text-sm text-foreground leading-snug">{task.title}</h3>
                      <div className="mt-3 flex items-center justify-between text-xs font-semibold text-muted-foreground">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-1" title="마감일">
                            <CalendarDays className="size-3.5" />
                            <span className={task.due.includes('오늘') ? 'text-red-500' : ''}>{task.due}</span>
                          </div>
                          <div className="flex items-center gap-1 hover:text-primary transition-colors cursor-pointer" title="이메일 출처 바로가기">
                            {col.id === 'blocked' ? <AlertCircle className="size-3.5" /> : <Inbox className="size-3.5" />}
                            <span className="underline decoration-muted-foreground/30 underline-offset-2">{task.source}</span>
                          </div>
                        </div>
                        <div className="flex items-center justify-center size-6 rounded-full bg-primary/10 text-primary" title={task.assignee}>
                          <User className="size-3.5" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="p-3 border-t border-border">
                  <button className="flex w-full items-center justify-center gap-2 rounded-md py-1.5 text-sm font-semibold text-muted-foreground hover:bg-secondary hover:text-foreground">
                    <Plus className="size-4" /> 항목 추가
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        {viewMode === '내 작업' && (
          <div className="space-y-4 max-w-4xl mx-auto">
            <h2 className="font-bold text-lg mb-4">내 작업 (My Tasks)</h2>
            {Object.values(tasks).flat().filter(t => t.assignee === '김나루').map(task => (
              <div key={task.id} className="flex items-center justify-between p-4 rounded-xl border border-border bg-card shadow-sm hover:border-primary/50 transition-colors cursor-pointer" onClick={() => { setSelectedTaskId(task.id); setViewMode('작업 상세'); }}>
                <div className="flex items-center gap-4">
                  <div className={`size-3 rounded-full ${task.priority === 'urgent' ? 'bg-red-500' : task.priority === 'high' ? 'bg-orange-500' : 'bg-blue-500'}`}></div>
                  <div>
                    <h3 className="font-bold text-sm">{task.title}</h3>
                    <p className="text-xs text-muted-foreground mt-1">마감: {task.due} | 출처: {task.source}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-bold ${task.status === 'done' ? 'bg-green-100 text-green-700' : 'bg-secondary text-secondary-foreground'}`}>{task.status}</span>
              </div>
            ))}
          </div>
        )}

        {viewMode === '위임한 작업' && (
          <div className="space-y-4 max-w-4xl mx-auto">
            <h2 className="font-bold text-lg mb-4">위임한 작업 (Delegation)</h2>
            {Object.values(tasks).flat().filter(t => t.assignee !== '김나루').map(task => (
              <div key={task.id} className="flex items-center justify-between p-4 rounded-xl border border-border bg-card shadow-sm hover:border-primary/50 transition-colors cursor-pointer" onClick={() => { setSelectedTaskId(task.id); setViewMode('작업 상세'); }}>
                <div className="flex items-center gap-4">
                  <div className="size-8 rounded-full bg-primary/10 text-primary grid place-items-center text-xs font-bold">{task.assignee.charAt(0)}</div>
                  <div>
                    <h3 className="font-bold text-sm">{task.title}</h3>
                    <p className="text-xs text-muted-foreground mt-1">담당자: {task.assignee} | 마감: {task.due}</p>
                  </div>
                </div>
                <span className="px-2 py-1 rounded-full text-xs font-bold bg-secondary text-secondary-foreground">{task.status}</span>
              </div>
            ))}
          </div>
        )}

        {viewMode === '작업 상세' && (() => {
          const task = Object.values(tasks).flat().find(t => t.id === selectedTaskId);
          if (!task) return <div className="p-6 text-center text-muted-foreground">작업을 선택해주세요.</div>;
          
          const priorityText = task.priority === 'urgent' ? '긴급' : task.priority === 'high' ? '우선순위 높음' : task.priority === 'normal' ? '보통' : '낮음';
          const priorityColor = task.priority === 'urgent' ? 'text-red-500 bg-red-100' : task.priority === 'high' ? 'text-orange-500 bg-orange-100' : 'text-blue-500 bg-blue-100';

          return (
          <div className="max-w-4xl mx-auto bg-card border border-border rounded-2xl shadow-sm p-6">
            <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">{task.id}</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${priorityColor}`}>{priorityText}</span>
                </div>
                <h2 className="text-2xl font-bold">{task.title}</h2>
              </div>
              <button className="px-4 py-2 bg-primary text-primary-foreground text-sm font-bold rounded-lg hover:bg-primary/90">상태 변경</button>
            </div>
            
            <div className="grid grid-cols-3 gap-6 mb-6">
              <div>
                <p className="text-xs text-muted-foreground font-semibold mb-1">담당자</p>
                <div className="flex items-center gap-2">
                  <div className="size-6 rounded-full bg-primary/10 text-primary grid place-items-center"><User className="size-3" /></div>
                  <span className="text-sm font-bold">{task.assignee}</span>
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold mb-1">마감일</p>
                <div className={`flex items-center gap-2 text-sm font-bold ${task.due.includes('오늘') ? 'text-red-500' : ''}`}>
                  <CalendarDays className="size-4" /> {task.due}
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold mb-1">출처</p>
                <div className="flex items-center gap-2 text-sm font-bold hover:text-primary cursor-pointer underline underline-offset-2 decoration-muted-foreground/30">
                  <Inbox className="size-4" /> {task.source}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="font-bold text-base">작업 설명</h3>
              <div className="p-4 bg-secondary/30 rounded-xl text-sm leading-relaxed border border-border/50">
                {task.title}와 관련된 상세 작업 설명입니다.
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-border">
              <h3 className="font-bold text-base mb-4">활동 기록</h3>
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="size-8 rounded-full bg-primary/10 text-primary grid place-items-center shrink-0 text-xs font-bold">시</div>
                  <div className="flex-1 bg-secondary/30 rounded-xl p-3 border border-border/50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold">시스템</span>
                      <span className="text-xs text-muted-foreground">방금 전</span>
                    </div>
                    <p className="text-sm">작업이 생성되었습니다.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );})()}
      </main>
    </div>
  );
}
