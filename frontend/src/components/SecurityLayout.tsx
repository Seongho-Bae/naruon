"use client";

import { useState } from 'react';
import { ShieldCheck, Lock, Users, AlertOctagon, CheckCircle2, XCircle } from 'lucide-react';

export function SecurityLayout() {
  const [activeTab, setActiveTab] = useState<'접근 제어 (RBAC/ABAC)' | '감사 로그' | '세션 관리'>('접근 제어 (RBAC/ABAC)');

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground flex-col">
      <header className="flex h-20 shrink-0 items-center border-b border-border bg-card px-8">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <ShieldCheck className="size-6 text-primary" /> 보안 및 권한 (Security)
        </h1>
        <div className="ml-8 flex gap-2">
          {['접근 제어 (RBAC/ABAC)', '감사 로그', '세션 관리'].map((tab) => (
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
          
          {activeTab === '접근 제어 (RBAC/ABAC)' && (
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

          {activeTab !== '접근 제어 (RBAC/ABAC)' && (
            <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-border bg-card">
              <p className="text-muted-foreground font-semibold">{activeTab} 메뉴는 준비 중입니다.</p>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
