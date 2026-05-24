"use client";

import { useState } from 'react';
import { Plus, Search, Filter, FolderOpen, MoreHorizontal, FileText, CheckCircle2, User, Clock, AlertCircle, CalendarDays } from 'lucide-react';

const MOCK_PROJECTS = [
  { id: 'P-01', title: 'Naruon 2.0 런칭', status: '진행 중', progress: 68, category: '제품 개발' },
  { id: 'P-02', title: '엔터프라이즈 SSO 연동', status: '대기 중', progress: 15, category: '보안/인프라' },
  { id: 'P-03', title: 'Q2 마케팅 캠페인', status: '완료', progress: 100, category: '마케팅' },
];

const MOCK_MILESTONES = [
  { title: '베타 테스트 (내부)', date: '5/10 - 5/20', status: '완료' },
  { title: '출시 회의 및 리뷰', date: '5/23 - 5/25', status: '진행 중' },
  { title: '정식 배포 (GA)', date: '6/01 - 6/05', status: '대기 중' },
];

const MOCK_DECISIONS = [
  { id: 'D-01', title: 'OIDC Provider 선정', decision: 'Keycloak 대신 Casdoor 도입 결정 (통합 UI 사유)', date: '2일 전', author: '박지현 PM' },
  { id: 'D-02', title: '캘린더 연동 방식', decision: 'CalDAV 직접 연동 후 로컬 캐싱', date: '1주 전', author: '최서연 Developer' },
];

export function ProjectsLayout() {
  const [activeProject, setActiveProject] = useState(MOCK_PROJECTS[0]);

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground">
      {/* Left Sidebar - Project List */}
      <aside className="w-72 shrink-0 flex-col overflow-y-auto border-r border-border bg-card hidden lg:flex">
        <div className="p-4 border-b border-border">
          <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2.5 text-sm font-bold text-primary-foreground shadow-sm hover:bg-primary/90">
            <Plus className="size-4" />새 프로젝트
          </button>
          <div className="relative mt-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <input type="text" placeholder="프로젝트 검색..." className="h-9 w-full rounded-md border border-border bg-background pl-9 pr-4 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary" />
          </div>
        </div>
        
        <div className="flex-1 p-3 space-y-1">
          {MOCK_PROJECTS.map((proj) => (
            <div
              key={proj.id}
              onClick={() => setActiveProject(proj)}
              className={`cursor-pointer rounded-lg px-3 py-3 transition-colors ${activeProject.id === proj.id ? 'bg-secondary border border-primary/20' : 'hover:bg-secondary/50 border border-transparent'}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-muted-foreground">{proj.category}</span>
                <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${proj.status === '완료' ? 'bg-green-100 text-green-700' : proj.status === '진행 중' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-700'}`}>{proj.status}</span>
              </div>
              <h3 className="mt-1 font-bold text-sm text-foreground">{proj.title}</h3>
              <div className="mt-3 flex items-center gap-2">
                <div className="h-1.5 flex-1 rounded-full bg-border overflow-hidden">
                  <div className={`h-full ${proj.progress === 100 ? 'bg-green-500' : 'bg-primary'}`} style={{ width: `${proj.progress}%` }}></div>
                </div>
                <span className="text-xs font-semibold text-muted-foreground">{proj.progress}%</span>
              </div>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Project Area */}
      <main className="flex min-w-0 flex-1 flex-col bg-background">
        <header className="flex h-20 shrink-0 items-center justify-between border-b border-border px-6 bg-card">
          <div>
            <h1 className="sr-only">프로젝트 워크스페이스</h1>
            <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground mb-1">
              <span>{activeProject.category}</span>
              <span>/</span>
              <span>{activeProject.id}</span>
            </div>
            <h2 className="text-2xl font-bold">{activeProject.title}</h2>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-1.5 text-sm font-semibold hover:bg-secondary">
              <Filter className="size-4" /> 필터
            </button>
            <button className="flex items-center gap-2 rounded-md bg-primary px-4 py-1.5 text-sm font-bold text-primary-foreground hover:bg-primary/90">
              보고서 생성
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6 min-w-0">
            {/* Milestones */}
            <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
              <div className="border-b border-border p-5 flex items-center justify-between">
                <h2 className="font-bold text-lg">마일스톤 (Milestones)</h2>
                <button className="text-sm text-primary font-semibold hover:underline">추가</button>
              </div>
              <div className="p-5">
                <div className="relative border-l-2 border-border ml-3 space-y-6">
                  {MOCK_MILESTONES.map((ms, idx) => (
                    <div key={idx} className="relative pl-6">
                      <div className={`absolute -left-[9px] top-1 size-4 rounded-full border-2 border-card ${ms.status === '완료' ? 'bg-green-500' : ms.status === '진행 중' ? 'bg-primary' : 'bg-border'}`}></div>
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-bold text-sm">{ms.title}</h3>
                          <p className="text-xs text-muted-foreground mt-1"><Clock className="inline size-3 mr-1" />{ms.date}</p>
                        </div>
                        <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${ms.status === '완료' ? 'bg-green-100 text-green-700' : ms.status === '진행 중' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-700'}`}>{ms.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Decision Logs */}
            <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
              <div className="border-b border-border p-5 flex items-center justify-between bg-primary/5">
                <h2 className="font-bold text-lg text-primary">의사결정 로그</h2>
                <button className="text-sm text-primary font-semibold hover:underline">기록 추가</button>
              </div>
              <div className="divide-y divide-border">
                {MOCK_DECISIONS.map((log) => (
                  <div key={log.id} className="p-5 hover:bg-secondary/20 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-bold text-base flex items-center gap-2">
                        <CheckCircle2 className="size-4 text-emerald-500" />
                        {log.title}
                      </h3>
                      <span className="text-xs text-muted-foreground">{log.date}</span>
                    </div>
                    <div className="rounded-lg bg-background border border-border p-3 text-sm text-foreground">
                      {log.decision}
                    </div>
                    <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground font-semibold">
                      <User className="size-3.5" /> 승인자: {log.author}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Project Metadata */}
          <div className="col-span-1 space-y-6">
            <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
              <h2 className="font-bold text-base mb-4">프로젝트 개요</h2>
              <div className="space-y-4 text-sm">
                <div>
                  <p className="text-muted-foreground font-semibold mb-1">책임자 (Owner)</p>
                  <div className="flex items-center gap-2">
                    <div className="size-6 rounded-full bg-primary/20 text-primary grid place-items-center"><User className="size-3" /></div>
                    <span className="font-bold">최서연 Developer</span>
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground font-semibold mb-1">상태</p>
                  <span className="rounded px-2 py-1 text-xs font-bold bg-blue-100 text-blue-700">{activeProject.status}</span>
                </div>
                <div>
                  <p className="text-muted-foreground font-semibold mb-1">연결된 자원</p>
                  <ul className="space-y-2 mt-2">
                    <li className="flex items-center gap-2 text-primary font-semibold hover:underline cursor-pointer"><FolderOpen className="size-4" /> WebDAV 산출물 폴더</li>
                    <li className="flex items-center gap-2 text-primary font-semibold hover:underline cursor-pointer"><CalendarDays className="size-4" /> CalDAV 팀 캘린더</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
