"use client";

import { useState } from 'react';
import { Database, HardDrive, RefreshCw, FolderOpen, AlertCircle, FileText, CheckCircle2 } from 'lucide-react';

export function DataLayout() {
  const [activeTab, setActiveTab] = useState<'문서 저장소' | '수집 파이프라인' | '임베딩' | '품질 점검'>('문서 저장소');

  return (
    <div className="flex h-full min-w-0 min-h-0 bg-background text-foreground flex-col overflow-x-hidden">
      <header className="flex h-20 shrink-0 items-center border-b border-border bg-card px-4 md:px-8 overflow-hidden">
        <h1 className="text-xl md:text-2xl font-bold flex shrink-0 items-center gap-3">
          <Database className="size-6 text-primary" /> <span className="hidden sm:inline">데이터와 파일</span>
        </h1>
        <p className="sr-only">중복 반입과 thread 정리</p>
        <div className="ml-4 md:ml-8 flex flex-1 min-w-0 gap-2 overflow-x-auto pb-1 scrollbar-hide">
          {['문서 저장소', '수집 파이프라인', '임베딩', '품질 점검'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as unknown)}
              className={`whitespace-nowrap px-3 md:px-4 py-2 text-sm font-bold rounded-lg transition-colors shrink-0 ${activeTab === tab ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-secondary'}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </header>

      <main className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden p-4 md:p-8 bg-background">
        <div className="max-w-5xl mx-auto space-y-8">
          
          {activeTab === '문서 저장소' && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-6">
                <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="rounded-xl bg-blue-100 p-3"><HardDrive className="size-5 text-blue-700" /></div>
                    <div>
                      <h2 className="font-bold text-sm text-muted-foreground">로컬 캐시 (Vector DB)</h2>
                      <p className="text-xl font-bold">12.4 GB <span className="text-sm font-normal text-muted-foreground">/ 50 GB</span></p>
                    </div>
                  </div>
                  <div className="h-2 w-full rounded-full bg-border overflow-hidden">
                    <div className="h-full bg-blue-500 w-[25%]"></div>
                  </div>
                </div>
                
                <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="rounded-xl bg-green-100 p-3"><FolderOpen className="size-5 text-green-700" /></div>
                    <div>
                      <h2 className="font-bold text-sm text-muted-foreground">WebDAV 원본 (연동됨)</h2>
                      <p className="text-xl font-bold">1.2 TB <span className="text-sm font-normal text-muted-foreground">/ 무제한</span></p>
                    </div>
                  </div>
                  <div className="h-2 w-full rounded-full bg-border overflow-hidden">
                    <div className="h-full bg-green-500 w-[45%]"></div>
                  </div>
                </div>

                <div className="rounded-2xl border border-border bg-card p-6 shadow-sm flex items-center justify-between">
                  <div>
                    <h2 className="font-bold text-sm text-muted-foreground mb-1">인덱싱 상태</h2>
                    <p className="text-lg font-bold text-emerald-600 flex items-center gap-2"><CheckCircle2 className="size-5" /> 최적화됨</p>
                  </div>
                  <button className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-bold shadow-sm hover:bg-secondary">
                    수동 최적화
                  </button>
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="p-5 border-b border-border bg-secondary/30">
                  <h2 className="font-bold text-lg">최근 수집 로그 (Ingestion Logs)</h2>
                </div>
                <div className="divide-y divide-border">
                  {[
                    { source: '회사 IMAP', item: 'Q2 런칭 기획.pdf', status: '인덱싱 완료', time: '10분 전', icon: FileText, color: 'text-green-600 bg-green-100' },
                    { source: 'CalDAV', item: '주간 회의 일정', status: '동기화 완료', time: '1시간 전', icon: RefreshCw, color: 'text-blue-600 bg-blue-100' },
                    { source: '개인 IMAP', item: '대용량 첨부파일.zip', status: '용량 초과 (Skip)', time: '3시간 전', icon: AlertCircle, color: 'text-red-600 bg-red-100' },
                  ].map((log, i) => (
                    <div key={i} className="p-4 flex items-center justify-between hover:bg-secondary/10 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg ${log.color}`}><log.icon className="size-4" /></div>
                        <div>
                          <p className="font-bold text-sm">{log.item}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">출처: {log.source}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`text-xs font-bold px-2 py-1 rounded-full ${log.status.includes('완료') ? 'text-green-700 bg-green-100' : 'text-red-700 bg-red-100'}`}>{log.status}</span>
                        <p className="text-xs text-muted-foreground mt-1">{log.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab !== '문서 저장소' && (
            <div className="flex flex-col items-center justify-center py-24 text-center rounded-2xl border border-dashed border-border bg-card">
              <Database className="size-10 text-muted-foreground mb-4 opacity-50" />
              <h2 className="text-xl font-bold mb-2">{activeTab} 패널</h2>
              <p className="text-muted-foreground max-w-sm">
                Naruon AI가 접근할 수 있는 데이터 구조와 인덱싱 현황을 관리하는 패널이 곧 업데이트 됩니다.
              </p>
            </div>
          )}
          
        </div>
      </main>
    </div>
  );
}
