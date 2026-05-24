"use client";

import { Settings, User, Mail, Bell, Shield, Smartphone, Plus, Monitor } from 'lucide-react';
import { useWorkspaceStartupView, setWorkspaceStartupView } from '@/lib/workspace-preferences';
import { useState } from 'react';

export function SettingsLayout() {
  const [activeTab, setActiveTab] = useState<'기본 설정' | '커넥터 설정' | '프로필' | '알림' | '보안' | '모바일 기기'>('기본 설정');
  const startupView = useWorkspaceStartupView();

  const handleStartupViewChange = (view: 'dashboard' | 'email' | 'calendar') => {
    setWorkspaceStartupView(view);
  };

  return (
    <div className="flex h-full min-h-0 bg-background text-foreground flex-col">
      <header className="flex h-20 shrink-0 items-center border-b border-border bg-card px-8">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <Settings className="size-6 text-primary" /> 설정 (Settings)
        </h1>
        <p className="sr-only">Self-hosted Runner</p>
      </header>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left Sidebar - Settings Tabs */}
        <aside className="w-64 shrink-0 border-r border-border bg-card overflow-y-auto hidden md:block">
          <div className="p-4 space-y-1">
            {[
              { id: '기본 설정', icon: Monitor },
              { id: '커넥터 설정', icon: Mail },
              { id: '프로필', icon: User },
              { id: '알림', icon: Bell },
              { id: '보안', icon: Shield },
              { id: '모바일 기기', icon: Smartphone },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-colors ${activeTab === tab.id ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-secondary hover:text-foreground'}`}
              >
                <tab.icon className="size-4" /> {tab.id}
              </button>
            ))}
          </div>
        </aside>

        {/* Main Settings Area */}
        <main className="flex-1 overflow-y-auto p-8 bg-background">
          <div className="max-w-3xl space-y-8">
            
            {activeTab === '기본 설정' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-bold text-xl">기본 설정</h2>
                    <p className="text-sm text-muted-foreground mt-1">Naruon의 전반적인 동작과 시작 화면을 설정합니다.</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
                    <h3 className="font-bold text-lg mb-4">시작 화면 설정</h3>
                    <p className="text-sm text-muted-foreground mb-4">로그인 시 처음 보여질 메인 화면을 선택하세요.</p>
                    <div className="grid grid-cols-3 gap-4">
                      {[
                        { label: '대시보드', value: 'dashboard', desc: '오늘의 요약과 실행 항목' },
                        { label: '이메일', value: 'email', desc: '인박스 중심으로 확인' },
                        { label: '일정 관리', value: 'calendar', desc: '오늘의 회의와 스케줄 확인' }
                      ].map((view) => (
                        <button
                          key={view.value}
                          onClick={() => setWorkspaceStartupView(view.value as any)}
                          className={`flex flex-col items-start gap-1 rounded-xl border p-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
                            startupView === view.value
                              ? 'border-primary bg-primary/5 shadow-sm'
                              : 'border-border hover:bg-secondary hover:border-primary/50'
                          }`}
                        >
                          <span className={`font-bold ${startupView === view.value ? 'text-primary' : 'text-foreground'}`}>
                            {view.label}
                          </span>
                          <span className="text-xs text-muted-foreground">{view.desc}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === '커넥터 설정' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-bold text-xl">이메일 및 캘린더 커넥터</h2>
                    <p className="text-sm text-muted-foreground mt-1">Naruon Relay Proxy를 통해 외부 계정의 데이터를 수집하고 연동합니다.</p>
                  </div>
                  <button className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90">
                    <Plus className="size-4" /> 커넥터 추가
                  </button>
                </div>

                <div className="space-y-4">
                  {/* Connected Accounts */}
                  <div className="rounded-2xl border border-border bg-card p-5 shadow-sm flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="size-10 rounded-full bg-blue-100 grid place-items-center"><Mail className="size-5 text-blue-600" /></div>
                      <div>
                        <h3 className="font-bold text-base">Google Workspace (업무용)</h3>
                        <p className="text-sm text-muted-foreground">seongho@naruon.com • IMAP, SMTP, CalDAV 연동됨</p>
                      </div>
                    </div>
                    <button className="text-sm font-semibold border border-border px-4 py-2 rounded-lg hover:bg-secondary">설정 변경</button>
                  </div>

                  <div className="rounded-2xl border border-border bg-card p-5 shadow-sm flex items-center justify-between opacity-70">
                    <div className="flex items-center gap-4">
                      <div className="size-10 rounded-full bg-slate-100 grid place-items-center"><Mail className="size-5 text-slate-600" /></div>
                      <div>
                        <h3 className="font-bold text-base">개인 메일 (iCloud)</h3>
                        <p className="text-sm text-muted-foreground">seongho.bae@icloud.com • IMAP 수집만 됨 (일정 연동 제외)</p>
                      </div>
                    </div>
                    <button className="text-sm font-semibold border border-border px-4 py-2 rounded-lg hover:bg-secondary">설정 변경</button>
                  </div>
                </div>

                {/* Form Example */}
                <div className="mt-8 rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <h3 className="font-bold text-lg mb-4">IMAP 수동 설정 (사내 메일)</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-bold text-muted-foreground">IMAP 서버 주소</label>
                      <input type="text" placeholder="imap.example.com" className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-bold text-muted-foreground">포트 (SSL)</label>
                      <input type="text" defaultValue="993" className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <label className="text-sm font-bold text-muted-foreground">사용자 계정</label>
                      <input type="email" placeholder="user@company.com" className="w-full rounded-lg border border-border bg-background px-4 py-2 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                    </div>
                  </div>
                  <button className="mt-6 rounded-lg bg-foreground text-background px-6 py-2 text-sm font-bold hover:bg-foreground/90">연결 테스트</button>
                </div>
              </div>
            )}

            {activeTab !== '커넥터 설정' && activeTab !== '기본 설정' && (
              <div className="flex h-64 items-center justify-center rounded-2xl border border-dashed border-border bg-card">
                <p className="text-muted-foreground font-semibold">{activeTab} 메뉴는 준비 중입니다.</p>
              </div>
            )}
            
          </div>
        </main>
      </div>
    </div>
  );
}
