"use client";

import { useCallback, useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { ArrowLeft, Network, X } from 'lucide-react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { EmailList } from '@/components/EmailList';
import { EmailDetail } from '@/components/EmailDetail';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import { Button } from '@/components/ui/button';

const NetworkGraph = dynamic(() => import('@/components/NetworkGraph'), { ssr: false });

export default function Home() {
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null);
  const [relationshipPanelOpen, setRelationshipPanelOpen] = useState(false);
  const relationshipPanelRef = useRef<HTMLDivElement | null>(null);
  const relationshipOpenerRef = useRef<HTMLElement | null>(null);

  const openRelationshipPanel = useCallback(() => {
    relationshipOpenerRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setRelationshipPanelOpen(true);
  }, []);

  const closeRelationshipPanel = useCallback(() => {
    setRelationshipPanelOpen(false);
    requestAnimationFrame(() => relationshipOpenerRef.current?.focus());
  }, []);

  useEffect(() => {
    if (!relationshipPanelOpen) return;

    const firstFocusable = relationshipPanelRef.current?.querySelector<HTMLElement>('button, [href], input, textarea, select, [tabindex]:not([tabindex="-1"])');
    firstFocusable?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeRelationshipPanel();
        return;
      }

      if (event.key === 'Tab' && relationshipPanelRef.current) {
        const focusable = Array.from(
          relationshipPanelRef.current.querySelectorAll<HTMLElement>('button, [href], input, textarea, select, [tabindex]:not([tabindex="-1"])')
        ).filter((element) => !element.hasAttribute('disabled'));
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (!first || !last) return;

        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [closeRelationshipPanel, relationshipPanelOpen]);

  return (
    <DashboardLayout>
      <div className="h-full overflow-hidden rounded-2xl border border-border/80 bg-card shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
        <div className="h-full md:hidden">
          {selectedEmail === null ? (
            <EmailList onSelectEmail={setSelectedEmail} selectedEmailId={selectedEmail} />
          ) : (
            <div className="flex h-full flex-col">
              <div className="flex min-h-14 items-center gap-2 border-b bg-card px-3">
                <Button variant="ghost" size="icon-lg" onClick={() => setSelectedEmail(null)} aria-label="메일 목록으로 돌아가기">
                  <ArrowLeft className="size-4" aria-hidden="true" />
                </Button>
                <div>
                  <p className="text-sm font-bold">메일 상세</p>
                  <p className="text-xs text-muted-foreground">요약, 실행 항목, 답장 초안</p>
                </div>
              </div>
              <div className="min-h-0 flex-1">
                <EmailDetail emailId={selectedEmail} onOpenRelationshipContext={openRelationshipPanel} />
              </div>
            </div>
          )}
        </div>

        <div className="hidden h-full md:block">
          <ResizablePanelGroup orientation="horizontal" className="h-full items-stretch">
            <ResizablePanel defaultSize={34} minSize={28} maxSize={42}>
              <EmailList onSelectEmail={setSelectedEmail} selectedEmailId={selectedEmail} />
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={66} minSize={48}>
              <EmailDetail emailId={selectedEmail} onOpenRelationshipContext={openRelationshipPanel} />
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      </div>

      {relationshipPanelOpen ? (
        <div
          className="fixed inset-0 z-50 flex justify-end bg-slate-950/35 p-3 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="relationship-panel-title"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeRelationshipPanel();
          }}
        >
          <div ref={relationshipPanelRef} className="flex h-full w-full max-w-[440px] flex-col overflow-hidden rounded-3xl border bg-card shadow-2xl">
            <div className="flex items-start gap-3 border-b p-5">
              <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-primary/10 text-primary">
                <Network className="size-5" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">관계 맥락</p>
                <h2 id="relationship-panel-title" className="text-lg font-black tracking-tight text-[#0B132B]">관계 그래프 보기</h2>
                <p className="mt-1 text-sm leading-5 text-muted-foreground">선택한 메일과 연결된 사람, 스레드, 일정의 흐름을 확인합니다.</p>
              </div>
              <Button variant="ghost" size="icon-lg" onClick={closeRelationshipPanel} aria-label="관계 그래프 닫기">
                <X className="size-4" aria-hidden="true" />
              </Button>
            </div>
            <div className="border-b bg-primary/5 px-5 py-3 text-sm leading-6 text-slate-700">
              관계 그래프는 현재 접근 가능한 관계 데이터를 표시합니다. 선택한 메일의 사람과 주제를 기준으로 확인하세요.
            </div>
            <div className="min-h-0 flex-1 bg-gradient-to-b from-background to-[#22C55E]/5 p-4">
              <div className="h-full overflow-hidden rounded-2xl border bg-card">
                <NetworkGraph />
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </DashboardLayout>
  );
}
