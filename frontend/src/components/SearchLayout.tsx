"use client";

import { useState } from 'react';
import { Search, Filter, Mail, CalendarDays, FileText, UserRound, Network, Clock, ChevronRight, CheckCircle2 } from 'lucide-react';

const MOCK_RESULTS = [
  { id: 'R-01', title: 'Q2 런칭 캠페인 기획안.pdf', type: '문서', source: 'WebDAV / marketing', date: '오늘 오전 10:30', icon: FileText },
  { id: 'R-02', title: 'Re: 런칭 일정 변경 안내', type: '메일', source: '보낸 메일 / thread-892', date: '어제 오후 2:15', icon: Mail },
  { id: 'R-03', title: '출시 최종 리뷰 미팅', type: '일정', source: '회사 CalDAV', date: '5/23 (목) 14:00', icon: CalendarDays },
  { id: 'R-04', title: '박지현 PM', type: '사람', source: '조직도', date: '최근 연락 2시간 전', icon: UserRound },
];

export function SearchLayout() {
  const [activeResult, setActiveResult] = useState(MOCK_RESULTS[0]);

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground flex-col">
      {/* Top Search Bar */}
      <header className="flex h-20 shrink-0 items-center justify-center border-b border-border bg-card px-8">
        <div className="relative w-full max-w-3xl">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-5 text-primary" />
          <input 
            type="text" 
            placeholder="메일, 일정, 파일, 사람, 의사결정 로그 검색..." 
            defaultValue="런칭 캠페인"
            className="h-12 w-full rounded-full border-2 border-primary/20 bg-background pl-12 pr-12 text-base shadow-sm focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all" 
          />
          <button className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors">
            <Filter className="size-5" />
          </button>
        </div>
      </header>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left Panel - Search Results */}
        <aside className="w-[400px] shrink-0 border-r border-border bg-card overflow-y-auto hidden md:block">
          <div className="p-5 border-b border-border flex items-center justify-between">
            <h2 className="font-bold">통합 검색 결과</h2>
            <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-bold text-primary">24건</span>
          </div>
          
          <div className="flex gap-2 p-4 border-b border-border overflow-x-auto no-scrollbar">
            {['전체', '메일', '문서', '일정', '사람'].map((filter, i) => (
              <button key={filter} className={`shrink-0 rounded-full px-3 py-1 text-xs font-bold ${i === 0 ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground hover:bg-secondary/80'}`}>
                {filter}
              </button>
            ))}
          </div>

          <div className="divide-y divide-border">
            {MOCK_RESULTS.map((res) => {
              const Icon = res.icon;
              return (
                <div 
                  key={res.id} 
                  onClick={() => setActiveResult(res)}
                  className={`cursor-pointer p-4 transition-colors ${activeResult.id === res.id ? 'bg-secondary/50 border-l-4 border-primary' : 'hover:bg-secondary/20 border-l-4 border-transparent'}`}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1 rounded-md bg-background border border-border p-2">
                      <Icon className="size-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-sm truncate">{res.title}</h3>
                      <p className="text-xs text-muted-foreground mt-1 truncate">{res.source}</p>
                      <div className="mt-2 flex items-center gap-2">
                        <span className="text-[10px] font-bold text-muted-foreground bg-border/50 px-1.5 py-0.5 rounded">{res.type}</span>
                        <span className="text-[10px] text-muted-foreground"><Clock className="inline size-3 mr-0.5" />{res.date}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        {/* Right Panel - Context & Graph */}
        <main className="flex-1 overflow-y-auto bg-background p-8">
          <div className="max-w-4xl mx-auto space-y-8">
            
            {/* Detail Card */}
            <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="rounded-xl bg-primary/10 p-4">
                    <activeResult.icon className="size-8 text-primary" />
                  </div>
                  <div>
                    <span className="rounded px-2 py-0.5 text-xs font-bold bg-primary/10 text-primary mb-2 inline-block">{activeResult.type}</span>
                    <h1 className="text-2xl font-bold">{activeResult.title}</h1>
                    <p className="text-sm text-muted-foreground mt-1">{activeResult.source}</p>
                  </div>
                </div>
                <button className="rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90">
                  열기
                </button>
              </div>
              <div className="rounded-xl bg-secondary/30 p-4 text-sm text-foreground leading-relaxed border border-border">
                이 문서(메일/일정)는 Q2 마케팅 캠페인의 최종 런칭 계획을 포함하고 있습니다. 파일의 무결성이 검증되었으며 WebDAV를 통해 동기화되었습니다.
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              {/* Relationship Graph Mock */}
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col">
                <div className="flex items-center gap-2 mb-4">
                  <Network className="size-5 text-primary" />
                  <h2 className="font-bold text-lg">관계 그래프 (Context Graph)</h2>
                </div>
                <div className="flex-1 relative min-h-[250px] bg-secondary/10 rounded-xl border border-dashed border-border flex items-center justify-center overflow-hidden">
                  {/* SVG Nodes Mock */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    <line x1="50%" y1="50%" x2="20%" y2="20%" stroke="var(--naruon-border)" strokeWidth="2" strokeDasharray="4" />
                    <line x1="50%" y1="50%" x2="80%" y2="30%" stroke="var(--naruon-border)" strokeWidth="2" strokeDasharray="4" />
                    <line x1="50%" y1="50%" x2="50%" y2="80%" stroke="var(--naruon-border)" strokeWidth="2" />
                  </svg>
                  <div className="absolute top-[15%] left-[15%] size-12 rounded-full bg-blue-100 border-2 border-blue-500 grid place-items-center z-10"><UserRound className="size-5 text-blue-700" /></div>
                  <div className="absolute top-[25%] right-[15%] size-12 rounded-full bg-green-100 border-2 border-green-500 grid place-items-center z-10"><Mail className="size-5 text-green-700" /></div>
                  <div className="absolute bottom-[15%] left-[45%] size-12 rounded-full bg-purple-100 border-2 border-purple-500 grid place-items-center z-10"><CalendarDays className="size-5 text-purple-700" /></div>
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 size-16 rounded-full bg-primary border-4 border-card grid place-items-center shadow-lg z-20">
                    <activeResult.icon className="size-6 text-primary-foreground" />
                  </div>
                </div>
              </div>

              {/* Timeline Flow */}
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-6">
                  <Clock className="size-5 text-primary" />
                  <h2 className="font-bold text-lg">타임라인 (Timeline)</h2>
                </div>
                <div className="relative border-l-2 border-border ml-3 space-y-6">
                  <div className="relative pl-6">
                    <div className="absolute -left-[9px] top-1 size-4 rounded-full border-2 border-card bg-primary"></div>
                    <p className="text-xs text-primary font-bold mb-1">현재</p>
                    <h3 className="text-sm font-bold bg-secondary inline-block px-2 py-1 rounded">결과 항목 선택됨</h3>
                  </div>
                  <div className="relative pl-6">
                    <div className="absolute -left-[9px] top-1 size-4 rounded-full border-2 border-card bg-border"></div>
                    <p className="text-xs text-muted-foreground font-bold mb-1">어제 오전 11:20</p>
                    <h3 className="text-sm font-bold text-muted-foreground">박지현 PM이 런칭 일정을 승인함</h3>
                    <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1"><CheckCircle2 className="size-3" /> 의사결정 로그</p>
                  </div>
                  <div className="relative pl-6">
                    <div className="absolute -left-[9px] top-1 size-4 rounded-full border-2 border-card bg-border"></div>
                    <p className="text-xs text-muted-foreground font-bold mb-1">3일 전</p>
                    <h3 className="text-sm font-bold text-muted-foreground">초안 문서 생성 (WebDAV 반입)</h3>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  );
}
