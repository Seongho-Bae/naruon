"use client";

import { useState } from 'react';
import { Database, HardDrive, RefreshCw, FolderOpen, AlertCircle, FileText, CheckCircle2 } from 'lucide-react';

export function DataLayout() {
  const [activeTab, setActiveTab] = useState<'저장소' | '수집 큐' | 'WebDAV 매핑'>('저장소');

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground flex-col">
      <header className="flex h-20 shrink-0 items-center border-b border-border bg-card px-8">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <Database className="size-6 text-primary" /> 데이터 관리 (Data)
        </h1>
        <div className="ml-8 flex gap-2">
          {['저장소', '수집 큐', 'WebDAV 매핑'].map((tab) => (
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
          
          {activeTab === '저장소' && (
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

          {activeTab !== '저장소' && (
            <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-border bg-card">
              <p className="text-muted-foreground font-semibold">{activeTab} 메뉴는 준비 중입니다.</p>
            </div>
          )}
          
        </div>
      </main>
    </div>
  );
}
