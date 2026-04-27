import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

const emails = [
  { id: 1, subject: "Project Update", sender: "alice@example.com", snippet: "Here is the latest..." },
  { id: 2, subject: "Meeting Notes", sender: "bob@example.com", snippet: "Thanks for joining..." }
];

export function EmailList({ onSelectEmail }: { onSelectEmail: (id: number) => void }) {
  return (
    <ScrollArea className="h-full w-full border-r">
      <div className="p-4 space-y-4">
        {emails.map(email => (
          <Card key={email.id} className="cursor-pointer hover:bg-accent" onClick={() => onSelectEmail(email.id)}>
            <CardHeader className="p-4">
              <CardTitle className="text-sm font-medium">{email.subject}</CardTitle>
              <CardDescription className="text-xs">{email.sender}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}
