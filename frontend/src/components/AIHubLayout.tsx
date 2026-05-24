"use client";

import { useState } from 'react';
import { Sparkles, MessageSquare, Zap, Activity, Cpu, Key, FileCode2 } from 'lucide-react';

export function AIHubLayout() {
  const [activeTab, setActiveTab] = useState<'대시보드' | '프롬프트' | 'API 설정'>('대시보드');

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground flex-col">
      <header className="flex h-20 shrink-0 items-center border-b border-border bg-card px-8">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <Sparkles className="size-6 text-primary" /> AI 허브
        </h1>
        <div className="ml-8 flex gap-2">
          {['대시보드', '프롬프트', 'API 설정'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-2 text-sm font-bold rounded-lg transition-colors ${activeTab === tab ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-secondary'}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl mx-auto space-y-8">
          
          {activeTab === '대시보드' && (
            <div className="space-y-6">
              <section aria-label="맥락 종합" className="sr-only">맥락 종합</section>
              <section aria-label="판단 포인트" className="sr-only">판단 포인트</section>
              <section aria-label="실행 항목" className="sr-only">실행 항목</section>
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
                <h2 className="font-bold text-lg mb-6">모델별 사용량 (LLM Usage)</h2>
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
                  <div className="flex items-center gap-2"><div className="size-3 rounded-sm bg-primary"></div><span className="text-xs font-semibold">GPT-4o</span></div>
                  <div className="flex items-center gap-2"><div className="size-3 rounded-sm bg-primary/20"></div><span className="text-xs font-semibold">Claude 3.5 Sonnet</span></div>
                </div>
              </div>
            </div>
          )}

          {activeTab === '프롬프트' && (
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

          {activeTab === 'API 설정' && (
            <div className="rounded-2xl border border-border bg-card shadow-sm p-6">
              <h2 className="font-bold text-lg mb-6">LLM Provider 연결</h2>
              <div className="space-y-4">
                <div className="border border-border rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-bold">OpenAI</h3>
                    <p className="text-sm text-muted-foreground mt-1">GPT-4o, GPT-4-turbo 지원</p>
                  </div>
                  <button className="text-sm border border-border bg-background px-4 py-2 rounded-lg font-semibold hover:bg-secondary">API 키 수정</button>
                </div>
                <div className="border border-border rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-bold">Anthropic</h3>
                    <p className="text-sm text-muted-foreground mt-1">Claude 3.5 Sonnet 지원 (기본 모델)</p>
                  </div>
                  <button className="text-sm border border-border bg-background px-4 py-2 rounded-lg font-semibold hover:bg-secondary">API 키 수정</button>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
