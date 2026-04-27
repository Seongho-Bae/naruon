"use client";

import { useState } from 'react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { EmailList } from '@/components/EmailList';
import { EmailDetail } from '@/components/EmailDetail';
import NetworkGraph from '@/components/NetworkGraph';

export default function Home() {
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null);

  return (
    <DashboardLayout>
      <div className="flex h-full">
        {/* Left pane: Email List */}
        <div className="w-1/4 min-w-[250px]">
          <EmailList onSelectEmail={setSelectedEmail} />
        </div>
        
        {/* Middle pane: Email Detail */}
        <div className="w-2/4 border-r bg-background">
          <EmailDetail emailId={selectedEmail} />
        </div>
        
        {/* Right pane: Network Graph */}
        <div className="w-1/4 min-w-[300px] p-4 flex flex-col bg-muted/20">
          <h3 className="font-semibold mb-4">Network Graph</h3>
          <div className="flex-1 border rounded-lg overflow-hidden bg-background">
            <NetworkGraph />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}