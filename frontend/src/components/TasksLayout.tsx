"use client";

import { useState } from 'react';
import { Plus, Search, Filter, MoreHorizontal, User, CalendarDays, Inbox, AlertCircle } from 'lucide-react';

const MOCK_TASKS = {
  open: [
    { id: 'T-101', title: '고객사 A 제안서 검토', tags: ['우선순위 높음', '제안'], due: '오늘 마감', assignee: '김나루', source: 'Inbox' },
    { id: 'T-102', title: '디자인 시스템 업데이트 리뷰', tags: ['디자인', '리뷰'], due: '내일 마감', assignee: '김나루', source: 'Design Thread' },
  ],
  in_progress: [
    { id: 'T-103', title: 'Q2 리스크 점검 회의록 작성', tags: ['회의록', '리스크'], due: '5/27 마감', assignee: '김나루', source: 'Meeting' },
  ],
  blocked: [
    { id: 'T-104', title: '외부 API 연동 권한 승인 대기', tags: ['권한', '개발'], due: '기한 없음', assignee: '박지현', source: 'IT Support' },
  ],
  done: [
    { id: 'T-105', title: '주간 파트 미팅 준비', tags: ['미팅'], due: '완료됨', assignee: '김나루', source: 'Calendar' },
  ],
};

const KANBAN_COLUMNS = [
  { id: 'open', title: '접수', count: MOCK_TASKS.open.length, color: 'bg-blue-100 text-blue-700' },
  { id: 'in_progress', title: '진행', count: MOCK_TASKS.in_progress.length, color: 'bg-orange-100 text-orange-700' },
  { id: 'blocked', title: '차단', count: MOCK_TASKS.blocked.length, color: 'bg-red-100 text-red-700' },
  { id: 'done', title: '완료', count: MOCK_TASKS.done.length, color: 'bg-green-100 text-green-700' },
];

export function TasksLayout() {
  const [viewMode, setViewMode] = useState<'내 작업' | '위임한 작업' | '칸반' | '작업 상세'>('칸반');
  const [tasks, setTasks] = useState(MOCK_TASKS);
  const [draggedTask, setDraggedTask] = useState<{id: string, sourceCol: string} | null>(null);

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
      targetList.push(movedTask);

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
      <main className="flex-1 overflow-x-auto overflow-y-hidden p-6 bg-secondary/20">
        {viewMode === '칸반' && (
          <div className="flex h-full gap-6">
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
        {viewMode !== '칸반' && (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            {viewMode} 뷰는 아직 구현 중입니다.
          </div>
        )}
      </main>
    </div>
  );
}
