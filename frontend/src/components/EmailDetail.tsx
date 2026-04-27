import React from 'react';
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

import { Checkbox } from "@/components/ui/checkbox";

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
                <Checkbox className="mt-1" />
                <span className="font-medium">Review the backend API documentation</span>
              </li>
              <li className="flex items-start gap-2 rounded-md border p-3">
                <Checkbox className="mt-1" />
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
