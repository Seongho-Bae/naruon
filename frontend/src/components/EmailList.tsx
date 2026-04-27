import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

interface EmailItem {
  id: number;
  subject: string | null;
  sender: string;
  date: string;
  snippet: string;
  unread?: boolean;
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
    <div className="h-full flex flex-col border-r bg-background w-full">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-lg tracking-tight">Inbox</h2>
      </div>
      <ScrollArea className="flex-1 w-full">
        <div className="flex flex-col gap-2 p-4">
          {emails.length === 0 && !error && <div className="text-sm text-muted-foreground">No emails found.</div>}
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
                      <AvatarFallback>{email.sender ? email.sender.charAt(0).toUpperCase() : 'U'}</AvatarFallback>
                    </Avatar>
                    <div className="font-semibold truncate max-w-[120px]">{email.sender}</div>
                  </div>
                  <div className="ml-auto text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(email.date).toLocaleDateString()}
                  </div>
                </div>
                <div className="text-xs font-medium truncate w-full">{email.subject || '(No Subject)'}</div>
              </div>
              <div className="line-clamp-2 text-xs text-muted-foreground w-full">
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