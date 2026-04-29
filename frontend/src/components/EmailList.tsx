import React, { useEffect, useState } from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MessagesSquare } from "lucide-react";
import { formatEmailDate } from "@/lib/email-threading";

interface EmailItem {
  id: number;
  subject: string | null;
  sender: string;
  date?: string;
  snippet: string;
  unread?: boolean;
  thread_id?: string; // O3: email threading support
  reply_count?: number;
}

export function EmailList({
  onSelectEmail,
  selectedEmailId,
}: {
  onSelectEmail: (id: number) => void;
  selectedEmailId?: number | null;
}) {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const fetchEmails = async (query = "") => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      if (query.trim() === "") {
        const res = await fetch(`${apiUrl}/api/emails`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setEmails(data.emails || []);
      } else {
        setIsSearching(true);
        const res = await fetch(`${apiUrl}/api/search`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query }),
        });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setEmails(data.results || []);
      }
    } catch (err) {
      console.error("Error fetching emails:", err);
      setError("Failed to load emails.");
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Initial inbox fetch synchronizes client state with the backend.
    fetchEmails();
  }, []);

  return (
    <div className="h-full flex flex-col border-r bg-background w-full">
      <div className="p-4 border-b flex flex-col gap-4">
        <h2 className="font-semibold text-lg tracking-tight">Inbox</h2>
        <form 
          onSubmit={(e: React.FormEvent) => {
            e.preventDefault();
            fetchEmails(searchQuery);
          }}
          className="flex gap-2"
        >
          <label htmlFor="email-search" className="sr-only">Search emails</label>
          <Input 
            id="email-search"
            aria-label="Search emails"
            placeholder="Search emails..." 
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
          />
          <Button type="submit" disabled={isSearching || loading}>
            {isSearching ? "Searching..." : "Search"}
          </Button>
        </form>
      </div>
      <ScrollArea className="flex-1 w-full">
        <div className="flex flex-col gap-2 p-4">
          {loading ? (
            <div role="status" aria-live="polite" className="text-sm text-muted-foreground">Loading emails...</div>
          ) : error ? (
            <div role="alert" className="text-sm text-red-500">{error}</div>
          ) : emails.length === 0 ? (
            <div className="text-sm text-muted-foreground">No emails found.</div>
          ) : (
            emails.map((email: EmailItem) => {
              const selected = selectedEmailId === email.id;

              return (
              <button 
                key={email.id} 
                onClick={() => onSelectEmail(email.id)}
                aria-current={selected ? "true" : undefined}
                className={`flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${selected ? 'border-primary bg-accent' : ''}`}
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
                      {formatEmailDate(email.date)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 w-full">
                    <div className="text-xs font-medium truncate flex-1">{email.subject || '(No Subject)'}</div>
                    {email.reply_count && email.reply_count > 1 && (
                      <Badge variant="secondary" className="text-[10px] leading-none px-1 py-0 h-4 whitespace-nowrap flex items-center gap-1">
                        <MessagesSquare className="w-3 h-3" />
                        {email.reply_count} msgs
                      </Badge>
                    )}
                  </div>
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
              );
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
