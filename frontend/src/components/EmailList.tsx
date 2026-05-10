import React, { useEffect, useState } from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Mail, MessagesSquare, Search, Sparkles } from "lucide-react";
import { apiFetch } from "@/lib/api-client";
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
        const res = await apiFetch(`${apiUrl}/api/emails`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setEmails(data.emails || []);
      } else {
        setIsSearching(true);
        const res = await apiFetch(`${apiUrl}/api/search`, {
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
    <div className="h-full flex w-full flex-col border-r border-border/80 bg-card/95">
      <div className="border-b border-border/80 bg-gradient-to-br from-card via-card to-primary/5 p-4">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
              <Sparkles className="size-3.5" aria-hidden="true" />
              Naruon Mail
            </div>
            <h2 className="mt-1 text-2xl font-black tracking-tight text-foreground">받은편지함</h2>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">중요 메일을 맥락과 실행 흐름으로 정리합니다.</p>
          </div>
          <span className="grid size-10 shrink-0 place-items-center rounded-2xl bg-primary text-primary-foreground shadow-[0_12px_28px_rgba(37,99,255,0.28)]">
            <Mail className="size-5" aria-hidden="true" />
          </span>
        </div>
        <form
          onSubmit={(e: React.FormEvent) => {
            e.preventDefault();
            fetchEmails(searchQuery);
          }}
          className="flex gap-2"
        >
          <label htmlFor="email-search" className="sr-only">Search emails</label>
          <div className="relative min-w-0 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              id="email-search"
              aria-label="Search emails"
              placeholder="메일, 사람, 키워드 검색..."
              value={searchQuery}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
              className="h-10 rounded-xl border-input bg-background/80 pl-9 shadow-inner shadow-slate-950/[0.02]"
            />
          </div>
          <Button type="submit" disabled={isSearching || loading} className="h-10 rounded-xl px-4">
            {isSearching ? "검색 중" : "검색"}
          </Button>
        </form>
      </div>
      <ScrollArea className="flex-1 w-full">
        <div className="flex flex-col gap-3 p-4">
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
                className={`group relative flex min-h-[7.5rem] flex-col items-start gap-3 overflow-hidden rounded-2xl border p-3 text-left text-sm transition-all hover:-translate-y-0.5 hover:border-primary/35 hover:bg-primary/5 hover:shadow-md focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${selected ? 'border-primary/60 bg-primary/10 shadow-[0_16px_36px_rgba(37,99,255,0.14)]' : 'border-border bg-card'}`}
              >
                <span className={`absolute inset-y-3 left-0 w-1 rounded-r-full ${selected ? 'bg-primary' : 'bg-transparent group-hover:bg-primary/50'}`} aria-hidden="true" />
                <div className="flex w-full flex-col gap-1">
                  <div className="flex items-center">
                    <div className="flex items-center gap-2">
                      <Avatar className="h-8 w-8 border border-primary/10 bg-primary/10 text-primary">
                        <AvatarFallback>{email.sender ? email.sender.charAt(0).toUpperCase() : 'U'}</AvatarFallback>
                      </Avatar>
                      <div className="max-w-[140px] truncate font-bold text-foreground">{email.sender}</div>
                    </div>
                    <div className="ml-auto max-w-24 truncate text-right text-xs text-muted-foreground">
                      {formatEmailDate(email.date)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 w-full">
                    <div className="truncate text-sm font-bold flex-1 text-foreground">{email.subject || '(No Subject)'}</div>
                    {email.reply_count && email.reply_count > 1 && (
                      <Badge variant="secondary" className="h-5 whitespace-nowrap border border-primary/10 bg-primary/10 px-2 py-0 text-[10px] leading-none text-primary flex items-center gap-1">
                        <MessagesSquare className="w-3 h-3" />
                        {email.reply_count} msgs
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="line-clamp-2 w-full text-xs leading-5 text-muted-foreground">
                  {email.snippet}
                </div>
                {email.unread && (
                  <div className="flex items-center gap-2">
                    <Badge variant="default" className="bg-emerald-500 text-[10px] text-white">New</Badge>
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
