"use client";

import { useState } from 'react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { EmailList } from '@/components/EmailList';
import { EmailDetail } from '@/components/EmailDetail';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';
import dynamic from 'next/dynamic';
const NetworkGraph = dynamic(() => import('@/components/NetworkGraph'), { ssr: false });

export default function Home() {
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null);

  return (
    <DashboardLayout>
      <ResizablePanelGroup orientation="horizontal" className="h-full items-stretch">
        <ResizablePanel defaultSize={25} minSize={20}>
          <EmailList onSelectEmail={setSelectedEmail} selectedEmailId={selectedEmail} />
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={50} minSize={30}>
          <EmailDetail emailId={selectedEmail} />
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={25} minSize={20}>
          <div className="h-full flex flex-col p-4 bg-muted/20">
            <h3 className="font-semibold mb-4 text-sm uppercase text-muted-foreground tracking-wider">Network Graph</h3>
            <div className="flex-1 border rounded-lg bg-background overflow-hidden">
              <NetworkGraph />
            </div>
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </DashboardLayout>
  );
}
