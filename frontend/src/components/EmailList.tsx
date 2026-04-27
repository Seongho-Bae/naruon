import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface EmailItem {
  id: number;
  subject: string | null;
  sender: string;
  date: string;
  snippet: string;
}

export function EmailList({ onSelectEmail }: { onSelectEmail: (id: number) => void }) {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/emails')
      .then(res => res.json())
      .then(data => {
        setEmails(data.emails || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching emails:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading emails...</div>;
  }

  return (
    <ScrollArea className="h-full w-full border-r">
      <div className="p-4 space-y-4">
        {emails.length === 0 && <div className="text-sm text-muted-foreground">No emails found.</div>}
        {emails.map(email => (
          <Card key={email.id} className="cursor-pointer hover:bg-accent transition-colors" onClick={() => onSelectEmail(email.id)}>
            <CardHeader className="p-4">
              <CardTitle className="text-sm font-medium">{email.subject || '(No Subject)'}</CardTitle>
              <CardDescription className="text-xs truncate">{email.sender}</CardDescription>
              <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{email.snippet}</p>
            </CardHeader>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}
