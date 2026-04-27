# O3 Email Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a professional Email Dashboard UI using shadcn/ui components like Resizable panels.

**Architecture:** We will integrate shadcn/ui components (`resizable`, `badge`, `avatar`) to create a three-pane resizable layout (Email List, Email Detail, Network Graph). The `DashboardLayout` will provide the outer shell, and `page.tsx` will arrange the panes using `Resizable` components.

**Tech Stack:** React, Next.js, Tailwind CSS, shadcn/ui.

---

### Task 1: Install required shadcn/ui components

**Files:**
- Modify: `package.json`, `components.json`

**Step 1: Install components**

Run: `cd frontend && npx shadcn@latest add resizable badge avatar --yes`
Expected: Components are added to `frontend/src/components/ui/` and dependencies updated.

**Step 2: Commit**

```bash
cd frontend
git add .
git commit -m "chore(ui): add resizable, badge, avatar shadcn components"
```

### Task 2: Refactor page.tsx to use Resizable Panes

**Files:**
- Modify: `frontend/src/app/page.tsx`

**Step 1: Update page.tsx implementation**

```tsx
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
      <ResizablePanelGroup direction="horizontal" className="h-full items-stretch">
        <ResizablePanel defaultSize={25} minSize={20}>
          <EmailList onSelectEmail={setSelectedEmail} />
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
```

**Step 2: Run build to verify it passes**

Run: `cd frontend && npm run build`
Expected: Build successful

**Step 3: Commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat(ui): implement resizable panes in main dashboard"
```

### Task 3: Refactor EmailList for professional UI

**Files:**
- Modify: `frontend/src/components/EmailList.tsx`

**Step 1: Update EmailList implementation**

```tsx
import React from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

const emails = [
  { id: 1, subject: "Project Update", sender: "alice@example.com", name: "Alice", snippet: "Here is the latest update on the new feature...", date: "10:42 AM", unread: true },
  { id: 2, subject: "Meeting Notes", sender: "bob@example.com", name: "Bob", snippet: "Thanks for joining the sync today. Please find...", date: "Yesterday", unread: false }
];

export function EmailList({ onSelectEmail }: { onSelectEmail: (id: number) => void }) {
  return (
    <div className="h-full flex flex-col border-r bg-background">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-lg tracking-tight">Inbox</h2>
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-2 p-4">
          {emails.map(email => (
            <button 
              key={email.id} 
              onClick={() => onSelectEmail(email.id)}
              className="flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent"
            >
              <div className="flex w-full flex-col gap-1">
                <div className="flex items-center">
                  <div className="flex items-center gap-2">
                    <Avatar className="h-6 w-6">
                      <AvatarFallback>{email.name[0]}</AvatarFallback>
                    </Avatar>
                    <div className="font-semibold">{email.name}</div>
                  </div>
                  <div className="ml-auto text-xs text-muted-foreground">
                    {email.date}
                  </div>
                </div>
                <div className="text-xs font-medium">{email.subject}</div>
              </div>
              <div className="line-clamp-2 text-xs text-muted-foreground">
                {email.snippet}
              </div>
              {email.unread && (
                <div className="flex items-center gap-2">
                  <Badge variant="default" className="text-[10px]">New</Badge>
                </div>
              )}
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
```

**Step 2: Run build to verify it passes**

Run: `cd frontend && npm run build`
Expected: Build successful

**Step 3: Commit**

```bash
git add frontend/src/components/EmailList.tsx
git commit -m "feat(ui): update email list with shadcn styling"
```

### Task 4: Refactor EmailDetail for professional UI

**Files:**
- Modify: `frontend/src/components/EmailDetail.tsx`

**Step 1: Update EmailDetail implementation**

```tsx
import React from 'react';
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

export function EmailDetail({ emailId }: { emailId: number | null }) {
  if (!emailId) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-muted-foreground">
        <div className="max-w-sm">
          <h2 className="text-lg font-medium text-foreground">No email selected</h2>
          <p className="text-sm">Select an email from the list on the left to view its details, summary, and extracted tasks.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-start p-6">
        <div className="flex items-start gap-4 text-sm">
          <Avatar className="h-10 w-10">
            <AvatarFallback>AL</AvatarFallback>
          </Avatar>
          <div className="grid gap-1">
            <div className="font-semibold text-base">Project Update</div>
            <div className="line-clamp-1 text-xs">
              <span className="font-medium">Alice</span>
              <span className="text-muted-foreground"> (alice@example.com)</span>
            </div>
            <div className="line-clamp-1 text-xs text-muted-foreground">
              Reply-To: alice@example.com
            </div>
          </div>
        </div>
        <div className="ml-auto text-xs text-muted-foreground">
          Oct 22, 2026, 10:42 AM
        </div>
      </div>
      <Separator />
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-6 p-6">
          
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">AI Summary</h3>
              <Badge variant="secondary" className="text-[10px]">Generated</Badge>
            </div>
            <div className="rounded-md bg-muted/50 p-4 text-sm">
              Alice has shared the latest project update. The backend API is complete and testing will commence next week. We need to focus on integrating the new UI components.
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">Extracted Action Items</h3>
              <Badge variant="secondary" className="text-[10px]">2 Tasks</Badge>
            </div>
            <ul className="list-none space-y-2 text-sm">
              <li className="flex items-start gap-2 rounded-md border p-3">
                <input type="checkbox" className="mt-1" />
                <span className="font-medium">Review the backend API documentation</span>
              </li>
              <li className="flex items-start gap-2 rounded-md border p-3">
                <input type="checkbox" className="mt-1" />
                <span className="font-medium">Prepare frontend UI components for integration</span>
              </li>
            </ul>
          </div>

          <Separator />
          
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase text-muted-foreground tracking-wider">Original Message</h3>
            <div className="text-sm whitespace-pre-wrap">
              Hi team,

              Here is the latest update on the new feature. The backend API has been merged successfully.

              Please review the backend API documentation by tomorrow. We also need someone to prepare the frontend UI components for integration so we can start wiring things up.

              Thanks,
              Alice
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
```

**Step 2: Run build to verify it passes**

Run: `cd frontend && npm run build`
Expected: Build successful

**Step 3: Commit**

```bash
git add frontend/src/components/EmailDetail.tsx
git commit -m "feat(ui): update email detail with structured layout and ai sections"
```