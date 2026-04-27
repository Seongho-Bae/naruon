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
