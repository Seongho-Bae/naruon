import React, { useEffect, useState } from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Inbox, MessagesSquare, Paperclip, RefreshCw, Search, Star } from "lucide-react";

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

export function EmailList({ onSelectEmail, selectedEmail }: { onSelectEmail: (id: number) => void; selectedEmail?: number | null }) {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const filters = ['전체', '읽지 않음', '중요', '고객', '첨부', 'AI 추천'];

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
      setError("메일 목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  useEffect(() => {
    void Promise.resolve().then(() => fetchEmails());
  }, []);

  return (
    <div className="flex h-full w-full flex-col border-r bg-background">
      <div className="flex flex-col gap-4 border-b bg-card/80 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">Naruon Mail</p>
            <h2 className="text-2xl font-black tracking-tight text-[#0B132B]">받은편지함</h2>
            <p className="mt-1 text-xs text-muted-foreground">중요 메일을 맥락과 실행 흐름으로 정리합니다.</p>
          </div>
          <Button type="button" className="size-11 rounded-2xl" aria-label="메일 목록 새로고침" onClick={() => fetchEmails(searchQuery)} disabled={loading}>
            <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
          </Button>
        </div>
        <form 
          onSubmit={(e: React.FormEvent) => {
            e.preventDefault();
            fetchEmails(searchQuery);
          }}
          className="flex gap-2"
        >
          <div className="relative min-w-0 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              aria-label="메일 검색"
              className="pl-9"
              placeholder="키워드, 사람, 주제로 검색"
              value={searchQuery}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button type="submit" className="h-10 rounded-xl px-4" disabled={isSearching || loading}>
            {isSearching ? "검색 중" : "검색"}
          </Button>
        </form>
        <div className="flex gap-1.5 overflow-x-auto pb-1" aria-label="메일 필터">
          {filters.map((filter, index) => (
            <Button
              key={filter}
              type="button"
              variant={index === 0 ? 'default' : 'outline'}
              size="sm"
              className="h-8 shrink-0 rounded-full px-3 text-xs"
              aria-pressed={index === 0}
            >
              {filter}
            </Button>
          ))}
        </div>
      </div>
      <ScrollArea className="flex-1 w-full">
        <div className="flex flex-col gap-2 p-4">
          {loading ? (
            <div className="rounded-2xl border border-dashed bg-muted/40 p-6 text-sm text-muted-foreground">메일 흐름을 불러오는 중입니다...</div>
          ) : error ? (
            <div className="rounded-2xl border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive">
              <p className="font-medium">메일을 불러오지 못했습니다.</p>
              <p className="mt-1 text-xs text-destructive/80">API 서버 연결을 확인한 뒤 다시 시도하세요.</p>
              <Button className="mt-3" type="button" variant="outline" size="sm" onClick={() => fetchEmails(searchQuery)}>다시 시도</Button>
            </div>
          ) : emails.length === 0 ? (
            <div className="rounded-2xl border border-dashed bg-muted/30 p-6 text-center text-sm text-muted-foreground">
              <Inbox className="mx-auto mb-3 size-8 text-primary/60" aria-hidden="true" />
              <p className="font-medium text-foreground">표시할 메일이 없습니다.</p>
              <p className="mt-1 text-xs">검색어를 바꾸거나 동기화 상태를 확인하세요.</p>
            </div>
          ) : (
            emails.map((email: EmailItem) => (
              <button 
                key={email.id} 
                onClick={() => onSelectEmail(email.id)}
                aria-current={selectedEmail === email.id ? 'true' : undefined}
                className={`group relative flex w-full flex-col items-start gap-2 rounded-2xl border p-3 text-left text-sm transition-all hover:border-primary/35 hover:bg-accent/70 ${selectedEmail === email.id ? 'border-primary/50 bg-primary/8 shadow-[0_10px_35px_-28px_rgba(37,99,235,0.8)] before:absolute before:left-0 before:top-4 before:h-12 before:w-1 before:rounded-r-full before:bg-primary' : 'bg-card'}`}
              >
                <div className="flex w-full flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className="grid size-5 place-items-center rounded-md border bg-background text-muted-foreground" aria-hidden="true">
                      {email.unread ? <span className="size-2 rounded-full bg-primary" /> : <Star className="size-3" />}
                    </span>
                    <div className="flex min-w-0 items-center gap-2">
                      <Avatar className="h-6 w-6">
                        <AvatarFallback>{email.sender ? email.sender.charAt(0).toUpperCase() : 'U'}</AvatarFallback>
                      </Avatar>
                      <div className="max-w-[140px] truncate font-semibold">{email.sender}</div>
                    </div>
                    <div className="ml-auto text-xs text-muted-foreground whitespace-nowrap">
                      {email.date ? new Date(email.date).toLocaleDateString() : '날짜 없음'}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 w-full">
                    <div className="text-sm font-bold truncate flex-1 text-[#0B132B]">{email.subject || '(제목 없음)'}</div>
                    <Badge variant="outline" className="hidden text-[10px] sm:inline-flex">고객</Badge>
                    {email.reply_count && email.reply_count > 1 && (
                      <Badge variant="secondary" className="text-[10px] leading-none px-1 py-0 h-4 whitespace-nowrap flex items-center gap-1">
                        <MessagesSquare className="w-3 h-3" />
                        {email.reply_count}개
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="line-clamp-2 text-xs text-muted-foreground w-full">
                  {email.snippet}
                </div>
                <div className="flex items-center gap-2">
                  {email.unread && <Badge variant="default" className="text-[10px]">새 메일</Badge>}
                  <Badge variant="secondary" className="text-[10px]"><Paperclip className="size-3" aria-hidden="true" />첨부</Badge>
                  <Badge variant="secondary" className="text-[10px]">AI 추천</Badge>
                </div>
              </button>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
