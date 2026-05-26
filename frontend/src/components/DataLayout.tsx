"use client";

import { useState, useEffect } from 'react';
import { Database, HardDrive, RefreshCw, FolderOpen, AlertCircle, FileText, CheckCircle2, Server } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

export function DataLayout() {
  const [activeTab, setActiveTab] = useState<'문서 저장소' | '수집 파이프라인' | '임베딩' | '품질 점검'>('문서 저장소');

  interface WebdavAccount {
    account_id: number;
    server_url: string;
    username: string;
  }

  interface ProjectFolder {
    folder_id: number;
    project_name: string;
    webdav_path: string;
  }

  const [webdavAccounts, setWebdavAccounts] = useState<WebdavAccount[]>([]);
  const [projectFolders, setProjectFolders] = useState<ProjectFolder[]>([]);

  useEffect(() => {
    apiClient.get<WebdavAccount[]>('/api/webdav/accounts')
      .then(data => Array.isArray(data) && setWebdavAccounts(data))
      .catch(console.error);

    apiClient.get<ProjectFolder[]>('/api/webdav/folders')
      .then(data => Array.isArray(data) && setProjectFolders(data))
      .catch(console.error);
  }, []);

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
              onClick={() => setActiveTab(tab as '문서 저장소' | '수집 파이프라인' | '임베딩' | '품질 점검')}
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
                      <p className="text-xl font-bold">
                        {webdavAccounts.length > 0 ? `${webdavAccounts.length}개 계정` : '연결 없음'}
                      </p>
                    </div>
                  </div>
                  {webdavAccounts.map(acc => (
                    <div key={acc.account_id} className="flex items-center gap-2 text-sm text-muted-foreground mt-2 bg-secondary/50 p-2 rounded-lg">
                      <Server className="size-4" />
                      <span className="font-medium">{acc.server_url}</span> ({acc.username})
                    </div>
                  ))}
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
                  <h2 className="font-bold text-lg flex items-center gap-2"><FolderOpen className="size-5" /> AI 프로젝트 구조화된 첨부파일 (WebDAV)</h2>
                </div>
                <div className="p-4 grid grid-cols-2 md:grid-cols-3 gap-4">
                  {projectFolders.length > 0 ? projectFolders.map(folder => (
                    <div key={folder.folder_id} className="border border-border rounded-xl p-4 bg-background hover:bg-secondary/20 transition-colors">
                      <div className="flex items-center gap-3 mb-2">
                        <FolderOpen className="size-5 text-primary" />
                        <span className="font-bold truncate">{folder.project_name}</span>
                      </div>
                      <p className="text-xs text-muted-foreground break-all">{folder.webdav_path}</p>
                    </div>
                  )) : (
                    <p className="text-sm text-muted-foreground col-span-full">AI가 구조화한 프로젝트 폴더가 없습니다.</p>
                  )}
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

          {activeTab === '수집 파이프라인' && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <h2 className="font-bold text-lg mb-6">현재 파이프라인 진행률</h2>
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-bold">1. 데이터 추출 (WebDAV / IMAP)</span>
                      <span className="text-sm text-muted-foreground font-semibold">100% 완료</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div className="h-full bg-green-500 w-full"></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-bold">2. 청크 분할 (Chunking)</span>
                      <span className="text-sm text-primary font-semibold">진행 중 (85%)</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div className="h-full bg-primary w-[85%]"></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-bold text-muted-foreground">3. 벡터 임베딩 (Embedding)</span>
                      <span className="text-sm text-muted-foreground font-semibold">대기 중</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                      <div className="h-full bg-slate-300 w-0"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === '임베딩' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">활성 모델</p>
                  <p className="text-lg font-bold text-primary">text-embedding-3-large</p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">벡터 차원 (Dimensions)</p>
                  <p className="text-lg font-bold">3,072</p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">총 인덱싱 건수</p>
                  <p className="text-lg font-bold">28,401</p>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">QPS (초당 쿼리)</p>
                  <p className="text-lg font-bold">4.2</p>
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <h2 className="font-bold text-lg mb-4">임베딩 컬렉션 상태</h2>
                <div className="divide-y divide-border border border-border rounded-lg overflow-hidden">
                  <div className="grid grid-cols-4 bg-secondary/50 p-3 text-xs font-bold text-muted-foreground">
                    <div>컬렉션 명</div>
                    <div>청크 수</div>
                    <div>마지막 업데이트</div>
                    <div>상태</div>
                  </div>
                  <div className="grid grid-cols-4 p-3 text-sm items-center">
                    <div className="font-bold">emails_naruon</div>
                    <div>12,400</div>
                    <div className="text-muted-foreground">10분 전</div>
                    <div><span className="bg-green-100 text-green-700 px-2 py-0.5 rounded text-xs font-bold">정상</span></div>
                  </div>
                  <div className="grid grid-cols-4 p-3 text-sm items-center">
                    <div className="font-bold">docs_webdav</div>
                    <div>16,001</div>
                    <div className="text-muted-foreground">1시간 전</div>
                    <div><span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-bold">업데이트 중</span></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === '품질 점검' && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">인덱싱 실패</p>
                  <p className="text-xl font-bold text-red-500">23건</p>
                  <button className="mt-3 text-xs font-semibold text-primary hover:underline">재시도</button>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">고아(Orphaned) 청크</p>
                  <p className="text-xl font-bold text-orange-500">105건</p>
                  <button className="mt-3 text-xs font-semibold text-primary hover:underline">정리하기</button>
                </div>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="text-xs font-bold text-muted-foreground mb-1">임베딩 일치율 평균</p>
                  <p className="text-xl font-bold text-green-600">92.4%</p>
                  <button className="mt-3 text-xs font-semibold text-primary hover:underline">상세 리포트</button>
                </div>
              </div>
              <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="p-5 border-b border-border bg-secondary/30">
                  <h2 className="font-bold text-lg">품질 문제 항목</h2>
                </div>
                <div className="p-5 text-sm text-muted-foreground text-center">
                  발견된 심각한 데이터 품질 문제가 없습니다.
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
