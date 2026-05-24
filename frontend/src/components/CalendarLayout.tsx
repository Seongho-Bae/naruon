"use client";

import { useState } from 'react';
import { ChevronLeft, ChevronRight, Settings, Plus, Users, Video, Paperclip, Clock, CalendarDays, CheckCircle2, X } from 'lucide-react';

export function CalendarLayout() {
  const [viewMode, setViewMode] = useState<'월' | '주' | '일' | '일정목록'>('월');

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground">
      {/* Left Sidebar - Calendar List */}
      <aside className="w-64 shrink-0 flex-col overflow-y-auto border-r border-border bg-card p-4 hidden lg:flex">
        <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2.5 text-sm font-bold text-primary-foreground shadow-sm hover:bg-primary/90">
          <Plus className="size-4" />새 일정
        </button>

        <div className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xs font-bold text-muted-foreground">캘린더 목록</h2>
          </div>
          <ul className="space-y-3">
            {[
              { name: '김나루 (나)', color: 'bg-primary' },
              { name: 'Naruon PM 팀', color: 'bg-red-500' },
              { name: '제품 개발팀', color: 'bg-green-500' },
              { name: '마케팅팀', color: 'bg-purple-500' },
              { name: '회사 공용', color: 'bg-indigo-500' },
              { name: '공휴일', color: 'bg-slate-400' },
            ].map((cal) => (
              <li key={cal.name} className="flex items-center gap-3 text-sm">
                <input type="checkbox" defaultChecked className={`size-4 rounded border-border text-primary focus:ring-primary`} style={{ accentColor: cal.color }} />
                <span className="font-medium text-foreground">{cal.name}</span>
              </li>
            ))}
          </ul>
          <button className="mt-4 flex items-center gap-2 text-sm font-semibold text-primary">
            <Plus className="size-4" /> 캘린더 추가
          </button>
        </div>
      </aside>

      {/* Main Calendar Area */}
      <main className="flex min-w-0 flex-1 flex-col bg-background">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-border px-6 bg-card">
          <div className="flex items-center gap-4">
            <button className="rounded-md border border-border bg-background px-3 py-1.5 text-sm font-semibold">오늘</button>
            <div className="flex items-center gap-1">
              <button className="grid size-8 place-items-center rounded-md hover:bg-secondary"><ChevronLeft className="size-5" /></button>
              <button className="grid size-8 place-items-center rounded-md hover:bg-secondary"><ChevronRight className="size-5" /></button>
            </div>
            <h1 className="text-xl font-bold">일정 관리</h1>
            <h2 className="text-sm font-bold text-muted-foreground ml-2">2026년 5월</h2>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex overflow-hidden rounded-md border border-border">
              {['월', '주', '일', '일정목록'].map((mode) => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode as unknown)}
                  className={`px-4 py-1.5 text-sm font-semibold transition-colors ${viewMode === mode ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-secondary'}`}
                >
                  {mode}
                </button>
              ))}
            </div>
            <button className="grid size-9 place-items-center rounded-md border border-border bg-background hover:bg-secondary">
              <Settings className="size-5" />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6">
          <p className="sr-only">원본 계정 writeback 흐름</p>
          {viewMode === '월' && (
            <div className="h-full rounded-2xl border border-border bg-card shadow-sm flex flex-col overflow-hidden">
              <div className="grid grid-cols-7 border-b border-border bg-secondary/50 text-center text-sm font-semibold py-3">
                <div className="text-red-500">일</div><div>월</div><div>화</div><div>수</div><div>목</div><div>금</div><div className="text-blue-500">토</div>
              </div>
              <div className="grid grid-cols-7 grid-rows-5 flex-1 divide-x divide-y divide-border">
                {/* Simulated Grid Cells */}
                {Array.from({ length: 35 }).map((_, i) => (
                  <div key={i} className="p-2 min-h-[100px]">
                    <span className={`text-sm font-semibold ${i % 7 === 0 ? 'text-red-500' : i % 7 === 6 ? 'text-blue-500' : 'text-muted-foreground'}`}>{i < 31 ? i + 1 : ''}</span>
                    {i === 15 && <div className="mt-1 rounded bg-green-100 px-2 py-1 text-xs font-semibold text-green-700">10:00 제품 리뷰</div>}
                    {i === 22 && <div className="mt-1 rounded bg-orange-100 px-2 py-1 text-xs font-semibold text-orange-700">09:30 출시 회의</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
          {viewMode !== '월' && (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              {viewMode} 뷰는 아직 구현 중입니다.
            </div>
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
            <button className="grid size-8 place-items-center rounded-md hover:bg-secondary"><X className="size-4" /></button>
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
            <button className="text-xs text-primary font-semibold ml-auto hover:underline">위치 보기</button>
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
          <button className="flex-1 rounded-lg border border-border bg-background py-2 text-sm font-bold shadow-sm hover:bg-secondary">삭제</button>
          <button className="flex-1 rounded-lg border border-border bg-background py-2 text-sm font-bold shadow-sm hover:bg-secondary">복사</button>
          <button className="flex-1 rounded-lg bg-primary py-2 text-sm font-bold text-primary-foreground shadow-sm hover:bg-primary/90">수정</button>
        </div>
      </aside>
    </div>
  );
}
