"use client";

import { useState } from 'react';
import { ShieldCheck, Lock, Users, AlertOctagon, CheckCircle2, XCircle } from 'lucide-react';

export function SecurityLayout() {
  const [activeTab, setActiveTab] = useState<'보안 대시보드' | '접근 권한' | '감사 로그' | '외부 공유' | '정책'>('접근 권한');

  return (
    <div className="flex h-full min-w-0 min-h-0 bg-background text-foreground flex-col overflow-x-hidden">
      <header className="flex h-20 shrink-0 items-center border-b border-border bg-card px-4 md:px-8 overflow-hidden">
        <h1 className="text-xl md:text-2xl font-bold flex shrink-0 items-center gap-3">
          <ShieldCheck className="size-6 text-primary" /> <span className="hidden sm:inline">보안과 관리자</span>
        </h1>
        <p className="sr-only">관리자 경계</p>
        <div className="ml-4 md:ml-8 flex flex-1 min-w-0 gap-2 overflow-x-auto pb-1 scrollbar-hide">
          {['보안 대시보드', '접근 권한', '감사 로그', '외부 공유', '정책'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as '보안 대시보드' | '접근 권한' | '감사 로그' | '외부 공유' | '정책')}
              className={`whitespace-nowrap px-3 md:px-4 py-2 text-sm font-bold rounded-lg transition-colors shrink-0 ${activeTab === tab ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-secondary'}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </header>

      <main className="flex-1 min-w-0 overflow-y-auto overflow-x-hidden p-4 md:p-8">
        <div className="max-w-5xl mx-auto space-y-8">
          
          {activeTab === '접근 권한' && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="font-bold text-lg">권한 정책 (Policies)</h2>
                    <p className="text-sm text-muted-foreground mt-1">사용자 역할(RBAC) 및 속성 기반(ABAC) 접근 제어 규칙입니다. <strong className="text-red-500">Deny 정책이 우선합니다.</strong></p>
                  </div>
                  <button className="bg-primary text-primary-foreground text-sm font-bold px-4 py-2 rounded-lg">새 정책 추가</button>
                </div>
                
                <div className="border border-border rounded-xl overflow-hidden">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-secondary/50 text-muted-foreground border-b border-border">
                      <tr>
                        <th className="p-4 font-bold">효과 (Effect)</th>
                        <th className="p-4 font-bold">대상 (Resource)</th>
                        <th className="p-4 font-bold">조건 (Condition / ABAC)</th>
                        <th className="p-4 font-bold">역할 (Role)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-background">
                      <tr className="hover:bg-secondary/20">
                        <td className="p-4"><span className="bg-red-100 text-red-700 px-2 py-1 rounded font-bold text-xs">DENY</span></td>
                        <td className="p-4 font-mono text-xs">/api/accounts/*</td>
                        <td className="p-4">Outside Corporate IP</td>
                        <td className="p-4">All</td>
                      </tr>
                      <tr className="hover:bg-secondary/20">
                        <td className="p-4"><span className="bg-green-100 text-green-700 px-2 py-1 rounded font-bold text-xs">ALLOW</span></td>
                        <td className="p-4 font-mono text-xs">/api/tasks/*</td>
                        <td className="p-4">Tenant == User.Tenant</td>
                        <td className="p-4">Member, Admin</td>
                      </tr>
                      <tr className="hover:bg-secondary/20">
                        <td className="p-4"><span className="bg-green-100 text-green-700 px-2 py-1 rounded font-bold text-xs">ALLOW</span></td>
                        <td className="p-4 font-mono text-xs">/api/settings/*</td>
                        <td className="p-4">-</td>
                        <td className="p-4">Admin</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="rounded-xl bg-orange-100 p-3"><AlertOctagon className="size-5 text-orange-700" /></div>
                    <h2 className="font-bold text-lg">최근 차단 로그</h2>
                  </div>
                  <div className="space-y-3">
                    {[
                      { user: 'guest@example.com', path: '/api/accounts', reason: 'Role mismatch' },
                      { user: 'park@naruon.com', path: '/api/tasks/T-102', reason: 'Tenant mismatch (ABAC)' },
                    ].map((log, i) => (
                      <div key={i} className="text-sm p-3 border border-border rounded-lg bg-background flex justify-between items-center">
                        <div>
                          <p className="font-bold">{log.user}</p>
                          <p className="text-xs text-muted-foreground font-mono mt-1">{log.path}</p>
                        </div>
                        <span className="text-xs text-red-600 bg-red-100 px-2 py-1 rounded font-bold">{log.reason}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="rounded-xl bg-purple-100 p-3"><Lock className="size-5 text-purple-700" /></div>
                    <h2 className="font-bold text-lg">인증 연동 (OIDC)</h2>
                  </div>
                  <div className="space-y-4 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-muted-foreground">Provider</span>
                      <span className="font-bold">Keycloak (Default)</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-muted-foreground">상태</span>
                      <span className="flex items-center gap-1 text-emerald-600 font-bold"><CheckCircle2 className="size-4" /> 연동됨</span>
                    </div>
                    <button className="w-full mt-2 py-2 border border-border rounded-lg font-bold hover:bg-secondary">
                      Casdoor로 마이그레이션
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === '보안 대시보드' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <h2 className="font-bold text-lg mb-6 flex items-center gap-2">
                    <AlertOctagon className="size-5 text-red-500" /> 위협 현황 (Threat Status)
                  </h2>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 rounded-lg border border-border bg-background">
                      <div className="flex items-center gap-3">
                        <div className="size-2 rounded-full bg-red-500"></div>
                        <div>
                          <p className="text-sm font-bold">비정상 로그인 시도 감지</p>
                          <p className="text-xs text-muted-foreground mt-0.5">외부 IP (14.xx.xx.xx)에서 관리자 계정 시도</p>
                        </div>
                      </div>
                      <span className="text-xs font-bold text-red-600 bg-red-100 px-2 py-1 rounded">High</span>
                    </div>
                    <div className="flex justify-between items-center p-3 rounded-lg border border-border bg-background">
                      <div className="flex items-center gap-3">
                        <div className="size-2 rounded-full bg-orange-500"></div>
                        <div>
                          <p className="text-sm font-bold">비인가 API 접근 차단</p>
                          <p className="text-xs text-muted-foreground mt-0.5">/api/settings 경로 접근 실패</p>
                        </div>
                      </div>
                      <span className="text-xs font-bold text-orange-600 bg-orange-100 px-2 py-1 rounded">Medium</span>
                    </div>
                    <div className="flex justify-between items-center p-3 rounded-lg border border-border bg-background">
                      <div className="flex items-center gap-3">
                        <div className="size-2 rounded-full bg-green-500"></div>
                        <div>
                          <p className="text-sm font-bold">전체 시스템 상태</p>
                          <p className="text-xs text-muted-foreground mt-0.5">현재 감지된 심각한 위협 없음</p>
                        </div>
                      </div>
                      <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-1 rounded">Safe</span>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <h2 className="font-bold text-lg mb-4">규정 준수 (Compliance)</h2>
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="size-5 text-emerald-500 shrink-0" />
                      <div>
                        <p className="text-sm font-bold">데이터 암호화 (At Rest)</p>
                        <p className="text-xs text-muted-foreground">PostgreSQL TDE 활성화됨</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="size-5 text-emerald-500 shrink-0" />
                      <div>
                        <p className="text-sm font-bold">통신 암호화 (In Transit)</p>
                        <p className="text-xs text-muted-foreground">TLS 1.3 강제 적용됨</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <XCircle className="size-5 text-red-500 shrink-0" />
                      <div>
                        <p className="text-sm font-bold">정기 접근 권한 리뷰</p>
                        <p className="text-xs text-muted-foreground">90일 초과됨 (리뷰 필요)</p>
                      </div>
                    </div>
                  </div>
                  <button className="w-full mt-6 py-2 border border-border rounded-lg text-sm font-bold hover:bg-secondary">
                    체크리스트 상세 보기
                  </button>
                </div>
              </div>
            </div>
          )}

          {(activeTab !== '접근 권한' && activeTab !== '보안 대시보드') && (
            <div className="flex flex-col items-center justify-center py-24 text-center rounded-2xl border border-dashed border-border bg-card">
              <ShieldCheck className="size-10 text-muted-foreground mb-4 opacity-50" />
              <h2 className="text-xl font-bold mb-2">{activeTab} 패널</h2>
              <p className="text-muted-foreground max-w-sm">
                조직 내 보안 현황, 감사 로그, 외부 공유 제한 등을 통제할 수 있는 기능이 곧 제공됩니다.
              </p>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
