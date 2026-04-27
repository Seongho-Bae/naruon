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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/api/emails`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        setEmails(data.emails || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching emails:", err);
        setError("Failed to load emails.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading emails...</div>;
  }

  if (error) {
    return <div className="p-4 text-sm text-red-500">{error}</div>;
  }

  return (
    <ScrollArea className="h-full w-full border-r">
      <div className="p-4 space-y-4">
        {emails.length === 0 && !error && <div className="text-sm text-muted-foreground">No emails found.</div>}
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
