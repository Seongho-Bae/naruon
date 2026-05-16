"use client";

import { useState } from 'react';

import { EmailList } from '@/components/EmailList';
import { EmailDetail } from '@/components/EmailDetail';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import dynamic from 'next/dynamic';
import { Network } from 'lucide-react';
import { setMobileWorkspaceView, useMobileWorkspaceView } from '@/lib/mobile-workspace';
const NetworkGraph = dynamic(() => import('@/components/NetworkGraph'), { ssr: false });

export default function Home() {
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null);
  const mobileView = useMobileWorkspaceView();
  const handleSelectEmail = (emailId: number) => {
    setSelectedEmail(emailId);
    setMobileWorkspaceView('detail');
  };

  return (
    <>
      <ResizablePanelGroup role="region" aria-label="데스크톱 메일 작업공간" orientation="horizontal" className="hidden h-full items-stretch rounded-3xl border border-border/80 bg-card/70 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl lg:flex">
          <ResizablePanel defaultSize={27} minSize={22}>
            <EmailList onSelectEmail={handleSelectEmail} selectedEmailId={selectedEmail} />
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={48} minSize={34}>
            <EmailDetail emailId={selectedEmail} />
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={25} minSize={20}>
            <div className="h-full flex flex-col bg-gradient-to-b from-primary/5 via-background to-emerald-500/5 p-4">
              <div className="mb-4 rounded-2xl border border-primary/15 bg-card p-4 shadow-sm">
                <div className="flex items-center gap-2">
                  <span className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary">
                    <Network className="size-4" aria-hidden="true" />
                  </span>
                  <div>
                    <h3 className="font-bold text-sm text-foreground">맥락 그래프</h3>
                    <p className="text-xs text-muted-foreground">메일과 관계의 흐름을 시각화합니다.</p>
                  </div>
                </div>
              </div>
              <div className="flex-1 overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
                <NetworkGraph />
              </div>
            </div>
          </ResizablePanel>
      </ResizablePanelGroup>
      <div className="h-full overflow-hidden rounded-3xl border border-border/80 bg-card/70 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl lg:hidden">
          <section
            id="mobile-inbox"
            aria-label="모바일 받은편지함"
            role="region"
            className={`mobile-workspace-panel mobile-workspace-panel-inbox h-full ${mobileView === 'inbox' ? 'block' : 'hidden'}`}
          >
            <EmailList onSelectEmail={handleSelectEmail} selectedEmailId={selectedEmail} />
          </section>
          <section
            id="mobile-detail"
            aria-label="모바일 메일 상세"
            role="region"
            className={`mobile-workspace-panel h-full flex-col ${mobileView === 'detail' && selectedEmail !== null ? 'flex' : 'hidden'}`}
          >
            <div className="p-3 border-b border-border bg-card">
              <button 
                onClick={() => {
                  setSelectedEmail(null);
                  setMobileWorkspaceView('inbox');
                }}
                className="text-sm font-semibold text-primary flex items-center gap-1"
              >
                ← 목록으로
              </button>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              <EmailDetail emailId={selectedEmail} />
            </div>
          </section>
          <section
            id="mobile-search"
            aria-label="모바일 맥락 검색"
            role="region"
            className={`mobile-workspace-panel mobile-workspace-panel-search h-full ${mobileView === 'search' ? 'flex' : 'hidden'} flex-col bg-gradient-to-b from-primary/5 via-background to-card p-4`}
          >
            <div className="rounded-2xl border border-primary/15 bg-card p-4 shadow-sm">
              <p className="text-xs font-bold text-primary">맥락 검색</p>
              <h2 className="mt-2 text-lg font-black text-foreground">메일, 첨부, 일정, 사람을 한 번에 검색합니다.</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                흩어진 대화와 파일을 하나의 판단 흐름으로 묶어 보여주는 모바일 검색 진입점입니다.
              </p>
            </div>
            <div className="mt-4 grid gap-3">
              {['메일', '첨부', '일정', '사람'].map((label) => (
                <div key={label} className="rounded-2xl border border-border bg-card px-4 py-3 text-sm font-semibold text-foreground shadow-sm">
                  {label} 결과 준비 중
                </div>
              ))}
            </div>
          </section>
          <section
            id="mobile-actions"
            aria-label="모바일 AI 실행"
            role="region"
            className={`mobile-workspace-panel mobile-workspace-panel-actions h-full ${mobileView === 'actions' ? 'flex' : 'hidden'} flex-col bg-gradient-to-b from-primary/5 via-background to-emerald-500/5 p-4`}
          >
            <div className="mb-4 rounded-2xl border border-primary/15 bg-card p-4 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Network className="size-4" aria-hidden="true" />
                </span>
                <div>
                  <h3 className="font-bold text-sm text-foreground">관계 맥락</h3>
                  <p className="text-xs text-muted-foreground">메일과 관계의 흐름을 시각화합니다.</p>
                </div>
              </div>
            </div>
            <div className="min-h-0 flex-1 overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
              {mobileView === 'actions' && <NetworkGraph />}
            </div>
          </section>
          <section
            id="mobile-calendar"
            aria-label="모바일 일정 연결"
            role="region"
            className={`mobile-workspace-panel mobile-workspace-panel-calendar h-full ${mobileView === 'calendar' ? 'flex' : 'hidden'} flex-col bg-gradient-to-b from-primary/5 via-background to-card p-4`}
          >
            <div className="rounded-2xl border border-primary/15 bg-card p-4 shadow-sm">
              <p className="text-xs font-bold text-primary">일정 연결</p>
              <h2 className="mt-2 text-lg font-black text-foreground">캘린더 반영 대기</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                메일에서 추출한 회의, 마감, 후속 조치를 모바일에서 바로 확인합니다.
              </p>
            </div>
            <div className="mt-4 space-y-3">
              {['Q2 출시 우선순위 회의', '벤더 계약 검토', '디자인 리뷰 후속 조치'].map((title) => (
                <article key={title} className="rounded-2xl border border-border bg-card p-4 shadow-sm">
                  <p className="text-sm font-bold text-foreground">{title}</p>
                  <p className="mt-1 text-xs text-muted-foreground">오늘 안에 일정 연결 검토가 필요합니다.</p>
                </article>
              ))}
            </div>
          </section>
      </div>
    </>
  );
}
