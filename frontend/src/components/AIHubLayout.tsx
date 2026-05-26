"use client";

import { useState } from 'react';
import { Sparkles, Zap, Activity, Cpu, Key, FileCode2 } from 'lucide-react';

const EXECUTION_SECTIONS = [
  {
    id: 'context',
    title: '맥락 종합',
    status: '7개 근거 연결',
    primary: '메일 thread-892, 회사 CalDAV 일정, WebDAV 산출물을 하나의 실행 후보로 묶었습니다.',
    secondary: '중복 메일과 전달본은 원본 메시지 식별자 기준으로 thread에 귀속됩니다.',
    action: '근거 열기',
  },
  {
    id: 'decisions',
    title: '판단 포인트',
    status: '3건 검토 대기',
    primary: '발신자 DAG와 프로젝트 의사결정 로그를 비교해 승인자, 위임자, 참조자를 분리합니다.',
    secondary: '조직, 개인, SOHO 계정의 RBAC/ABAC 경계를 함께 평가합니다.',
    action: '판단 기록',
  },
  {
    id: 'actions',
    title: '실행 항목',
    status: '5개 워크플로우',
    primary: '일정 후보, 티켓형 작업, 답장 추적을 원본 계정 writeback 대상과 함께 큐에 올립니다.',
    secondary: 'Naruon 저장소만 남기는 항목은 만들지 않고 원본 CalDAV/WebDAV/메일 계정을 우선합니다.',
    action: '큐 확인',
  },
] as const;

export function AIHubLayout() {
  const [activeTab, setActiveTab] = useState<'프롬프트 스튜디오' | '워크플로우' | 'AI 에이전트' | '평가' | '실행 이력'>('워크플로우');

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground flex-col">
      <header className="flex h-20 shrink-0 items-center border-b border-border bg-card px-8">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <Sparkles className="size-6 text-primary" /> AI 허브
        </h1>
        <div className="ml-8 flex gap-2 overflow-x-auto no-scrollbar">
          {['프롬프트 스튜디오', '워크플로우', 'AI 에이전트', '평가', '실행 이력'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as '프롬프트 스튜디오' | '워크플로우' | 'AI 에이전트' | '평가' | '실행 이력')}
              className={`whitespace-nowrap px-4 py-2 text-sm font-bold rounded-lg transition-colors ${activeTab === tab ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-secondary'}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl mx-auto space-y-8">
          <nav aria-label="AI hub execution checkpoints" className="flex scroll-smooth gap-2 overflow-x-auto pb-1">
            {EXECUTION_SECTIONS.map((section) => (
              <a
                key={section.id}
                href={`#${section.id}`}
                className="shrink-0 rounded-lg border border-border bg-card px-3 py-2 text-sm font-bold text-foreground hover:border-primary hover:text-primary"
              >
                {section.title}
              </a>
            ))}
          </nav>

          <div className="grid gap-4 lg:grid-cols-3">
            {EXECUTION_SECTIONS.map((section) => (
              <section
                id={section.id}
                key={section.id}
                aria-label={section.title}
                className="scroll-mt-24 rounded-2xl border border-border bg-card p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-bold">{section.title}</h2>
                    <p className="mt-1 text-xs font-bold text-primary">{section.status}</p>
                  </div>
                  <button type="button" className="shrink-0 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-bold hover:bg-secondary">
                    {section.action}
                  </button>
                </div>
                <p className="mt-4 text-sm leading-6 text-foreground">{section.primary}</p>
                <p className="mt-3 text-xs leading-5 text-muted-foreground">{section.secondary}</p>
              </section>
            ))}
          </div>
          
          {activeTab === '평가' && (
            <div className="space-y-6">
              {/* Token Usage Stats */}
              <div className="grid grid-cols-4 gap-6">
                {[
                  { label: '이번 달 호출 수', value: '4,208', icon: Activity, color: 'text-blue-500' },
                  { label: '사용된 토큰', value: '1.2M', icon: Cpu, color: 'text-purple-500' },
                  { label: '평균 응답 시간', value: '1.4s', icon: Zap, color: 'text-orange-500' },
                  { label: '토큰당 비용', value: '$0.002', icon: Key, color: 'text-green-500' },
                ].map((stat, i) => (
                  <div key={i} className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                    <stat.icon className={`size-5 ${stat.color} mb-3`} />
                    <p className="text-sm font-bold text-muted-foreground">{stat.label}</p>
                    <p className="text-2xl font-black mt-1">{stat.value}</p>
                  </div>
                ))}
              </div>

              {/* Usage Graph Mock */}
              <div className="rounded-2xl border border-border bg-card shadow-sm p-6">
                <h2 className="font-bold text-lg mb-6">모델별 평가 지표 (LLM Evaluation)</h2>
                <div className="h-64 flex items-end gap-4 justify-between border-b border-border pb-2 px-4 relative">
                  {/* Grid Lines */}
                  <div className="absolute inset-x-0 bottom-1/4 border-b border-dashed border-border z-0"></div>
                  <div className="absolute inset-x-0 bottom-2/4 border-b border-dashed border-border z-0"></div>
                  <div className="absolute inset-x-0 bottom-3/4 border-b border-dashed border-border z-0"></div>
                  
                  {[60, 80, 40, 90, 50, 70, 30].map((h, i) => (
                    <div key={i} className="w-full relative z-10 group flex flex-col justify-end items-center h-full">
                      <div className="w-12 bg-primary/20 rounded-t-sm hover:bg-primary/40 transition-colors" style={{ height: `${h}%` }}>
                        <div className="w-full bg-primary rounded-t-sm" style={{ height: `${h * 0.4}%` }}></div>
                      </div>
                      <span className="text-xs text-muted-foreground mt-2 font-semibold">5/{18 + i}</span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-4 justify-center mt-4">
                  <div className="flex items-center gap-2"><div className="size-3 rounded-sm bg-primary"></div><span className="text-xs font-semibold">GPT-4o 정확도</span></div>
                  <div className="flex items-center gap-2"><div className="size-3 rounded-sm bg-primary/20"></div><span className="text-xs font-semibold">Claude 3.5 정확도</span></div>
                </div>
              </div>
            </div>
          )}

          {activeTab === '프롬프트 스튜디오' && (
            <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
              <div className="p-5 border-b border-border bg-secondary/30 flex justify-between items-center">
                <h2 className="font-bold text-lg">시스템 프롬프트 관리</h2>
                <button className="bg-primary text-primary-foreground text-sm font-bold px-4 py-2 rounded-lg">새 프롬프트</button>
              </div>
              <div className="divide-y divide-border">
                {[
                  { name: '일정 추출 시스템', id: 'prompt-calendar-v2', desc: '이메일 본문에서 회의 시간, 장소, 참석자를 파싱합니다.', active: true },
                  { name: '의사결정 로그 요약', id: 'prompt-decision-v1', desc: '스레드 내에서 최종 승인자와 결정 사항을 요약합니다.', active: true },
                  { name: '자동 답장 초안 (톤앤매너)', id: 'prompt-reply-v4', desc: '이전 발신 메일을 바탕으로 어조를 맞춰 답장을 작성합니다.', active: false },
                ].map((prompt) => (
                  <div key={prompt.id} className="p-5 flex items-start justify-between">
                    <div className="flex gap-4">
                      <div className="p-3 bg-secondary rounded-xl h-fit"><FileCode2 className="size-5 text-primary" /></div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-bold text-base">{prompt.name}</h3>
                          {prompt.active ? 
                            <span className="bg-green-100 text-green-700 text-[10px] px-2 py-0.5 rounded font-bold">Active</span> :
                            <span className="bg-slate-100 text-slate-700 text-[10px] px-2 py-0.5 rounded font-bold">Draft</span>
                          }
                        </div>
                        <p className="text-sm text-muted-foreground">{prompt.desc}</p>
                        <p className="text-xs text-muted-foreground mt-2 font-mono">{prompt.id}</p>
                      </div>
                    </div>
                    <button className="text-sm font-semibold text-primary hover:underline">편집</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === '워크플로우' && (
            <div className="rounded-2xl border border-border bg-card shadow-sm p-6 h-[600px] flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <h2 className="font-bold text-lg">DAG 노드 캔버스 (Agent Workflow)</h2>
                <button className="text-sm border border-border bg-background px-4 py-2 rounded-lg font-semibold hover:bg-secondary">새 노드 추가</button>
              </div>
              <div className="flex-1 border border-border rounded-xl bg-secondary/10 relative overflow-hidden flex items-center justify-center">
                <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
                  <path d="M 150 200 C 300 200, 300 100, 450 100" stroke="var(--naruon-border)" strokeWidth="3" fill="none" />
                  <path d="M 150 200 C 300 200, 300 300, 450 300" stroke="var(--naruon-border)" strokeWidth="3" fill="none" />
                </svg>
                <div className="absolute left-[50px] top-[160px] w-48 rounded-lg bg-card border-2 border-primary p-3 shadow-md z-10">
                  <p className="text-xs font-bold text-primary mb-1">Trigger</p>
                  <p className="text-sm font-semibold">새 이메일 수신</p>
                </div>
                <div className="absolute left-[450px] top-[60px] w-48 rounded-lg bg-card border-2 border-border p-3 shadow-sm z-10">
                  <p className="text-xs font-bold text-muted-foreground mb-1">Action</p>
                  <p className="text-sm font-semibold">일정 추출 (LLM)</p>
                </div>
                <div className="absolute left-[450px] top-[260px] w-48 rounded-lg bg-card border-2 border-border p-3 shadow-sm z-10">
                  <p className="text-xs font-bold text-muted-foreground mb-1">Action</p>
                  <p className="text-sm font-semibold">지식 그래프 저장</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'AI 에이전트' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-bold">등록된 에이전트</h2>
                <button className="bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-bold">새 에이전트 등록</button>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { name: '일정 조율 에이전트', model: 'GPT-4o', status: '활성' },
                  { name: '의사결정 추출 에이전트', model: 'Claude 3.5 Sonnet', status: '활성' },
                  { name: '티켓 분류 에이전트', model: 'Gemini 1.5 Pro', status: '대기 중' },
                ].map((agent, i) => (
                  <div key={i} className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="font-bold">{agent.name}</h3>
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${agent.status === '활성' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'}`}>{agent.status}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-4">사용 모델: <span className="font-semibold text-foreground">{agent.model}</span></p>
                    <div className="flex gap-2">
                      <button className="flex-1 border border-border rounded-lg py-1.5 text-xs font-bold hover:bg-secondary">설정</button>
                      <button className="flex-1 border border-border rounded-lg py-1.5 text-xs font-bold hover:bg-secondary">테스트</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === '실행 이력' && (
            <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
              <div className="p-5 border-b border-border bg-secondary/30 flex justify-between items-center">
                <h2 className="font-bold text-lg">최근 실행 로그</h2>
              </div>
              <div className="divide-y divide-border">
                {[
                  { id: 'LOG-001', agent: '일정 조율 에이전트', trigger: '새 이메일', time: '5분 전', status: '성공' },
                  { id: 'LOG-002', agent: '의사결정 추출 에이전트', trigger: '스레드 업데이트', time: '12분 전', status: '성공' },
                  { id: 'LOG-003', agent: '티켓 분류 에이전트', trigger: '수동 실행', time: '1시간 전', status: '실패' },
                ].map((log, i) => (
                  <div key={i} className="p-4 flex items-center justify-between hover:bg-secondary/10">
                    <div>
                      <p className="font-bold text-sm">{log.agent} <span className="text-xs text-muted-foreground ml-2">{log.id}</span></p>
                      <p className="text-xs text-muted-foreground mt-1">트리거: {log.trigger}</p>
                    </div>
                    <div className="text-right">
                      <span className={`text-xs font-bold px-2 py-1 rounded-full ${log.status === '성공' ? 'text-green-700 bg-green-100' : 'text-red-700 bg-red-100'}`}>{log.status}</span>
                      <p className="text-xs text-muted-foreground mt-1">{log.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
