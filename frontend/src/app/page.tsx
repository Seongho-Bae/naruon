"use client";

import { useState } from 'react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { EmailList } from '@/components/EmailList';
import { EmailDetail } from '@/components/EmailDetail';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import dynamic from 'next/dynamic';
import { Network } from 'lucide-react';
const NetworkGraph = dynamic(() => import('@/components/NetworkGraph'), { ssr: false });

export default function Home() {
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null);

  return (
    <DashboardLayout>
      <ResizablePanelGroup orientation="horizontal" className="h-full items-stretch rounded-3xl border border-border/80 bg-card/70 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl">
        <ResizablePanel defaultSize={27} minSize={22}>
          <EmailList onSelectEmail={setSelectedEmail} selectedEmailId={selectedEmail} />
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
    </DashboardLayout>
  );
}
