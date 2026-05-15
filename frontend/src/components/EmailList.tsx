import React, { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { CheckCircle2, ChevronLeft, ChevronRight, Mail, MessagesSquare, Network, Search, Sparkles } from "lucide-react";
import { formatEmailDate } from "@/lib/email-threading";
import { markExecutionQueueItemDone, queueEmailExecutionItem } from '@/lib/execution-queue';

interface EmailItem {
  id: number;
  mailbox_account_id?: number | null;
  subject: string | null;
  sender: string;
  date?: string;
  snippet: string;
  unread?: boolean;
  thread_id?: string; // O3: email threading support
  reply_count?: number;
}

interface MailboxAccountItem {
  id: number;
  email_address: string;
  display_name: string | null;
  is_default_reply: boolean;
  is_active: boolean;
}

export function EmailList({
  onSelectEmail,
  selectedEmailId,
}: {
  onSelectEmail: (id: number, email?: EmailItem, mailboxAccountId?: number | null) => void;
  selectedEmailId?: number | null;
}) {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [mailboxAccounts, setMailboxAccounts] = useState<MailboxAccountItem[]>([]);
  const [selectedMailboxAccountId, setSelectedMailboxAccountId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [swipeOffsets, setSwipeOffsets] = useState<Record<number, number>>({});
  const [queueFeedback, setQueueFeedback] = useState<string | null>(null);
  const pointerStateRef = useRef<{ id: number; startX: number; startY: number } | null>(null);
  const suppressSelectionRef = useRef<number | null>(null);
  const swipeOffsetsRef = useRef<Record<number, number>>({});
  const capturedPointerIdsRef = useRef<Record<number, number>>({});

  const fetchEmails = useCallback(async (query = "", mailboxAccountId = selectedMailboxAccountId) => {
    setLoading(true);
    setError(null);
    try {
      if (query.trim() === "") {
        const params = mailboxAccountId ? `?mailbox_account_id=${mailboxAccountId}` : '';
        const data = await apiClient.get<{ emails: EmailItem[] }>(`/api/emails${params}`);
        setEmails(data.emails || []);
      } else {
        setIsSearching(true);
        const data = await apiClient.post<{ results: EmailItem[] }>('/api/search', {
          query,
          ...(mailboxAccountId ? { mailbox_account_id: mailboxAccountId } : {}),
        });
        setEmails(data.results || []);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load emails");
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  }, [selectedMailboxAccountId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Initial inbox fetch synchronizes client state with the backend.
    fetchEmails();
  }, [fetchEmails]);

  useEffect(() => {
    let active = true;
    const loadMailboxAccounts = async () => {
      try {
        const data = await apiClient.get<{ items: MailboxAccountItem[] }>('/api/mailbox-accounts');
        if (!active) return;
        setMailboxAccounts(data.items || []);
      } catch {
        if (!active) return;
        setMailboxAccounts([]);
      }
    };
    void loadMailboxAccounts();
    return () => {
      active = false;
    };
  }, []);

  const mailboxAccountLabel = (mailboxAccountId?: number | null) => {
    if (!mailboxAccountId) return null;
    const account = mailboxAccounts.find((item) => item.id === mailboxAccountId);
    return account ? (account.display_name || account.email_address) : null;
  };

  useEffect(() => {
    if (!queueFeedback) return;
    const timer = window.setTimeout(() => setQueueFeedback(null), 1800);
    return () => window.clearTimeout(timer);
  }, [queueFeedback]);

  const handleQueueEmail = useCallback(async (email: EmailItem) => {
    try {
      await queueEmailExecutionItem({ id: email.id, subject: email.subject, sender: email.sender });
      suppressSelectionRef.current = email.id;
      setQueueFeedback(`'${email.subject || '(제목 없음)'}' 메일을 실행 목록에 담았습니다.`);
    } catch {
      setQueueFeedback(`'${email.subject || '(제목 없음)'}' 메일을 실행 목록에 담지 못했습니다.`);
    }
  }, []);

  const handleCompleteEmail = useCallback(async (email: EmailItem) => {
    try {
      const doneItem = await markExecutionQueueItemDone(email.id);
      if (doneItem) {
        suppressSelectionRef.current = email.id;
        setQueueFeedback(`'${doneItem.title}' 항목을 완료 처리했습니다.`);
      }
    } catch {
      setQueueFeedback(`'${email.subject || '(제목 없음)'}' 항목을 완료 처리하지 못했습니다.`);
    }
  }, []);

  const handlePointerDown = (emailId: number) => (event: React.PointerEvent<HTMLButtonElement>) => {
    pointerStateRef.current = {
      id: emailId,
      startX: event.clientX,
      startY: event.clientY,
    };
  };

  const handlePointerMove = (emailId: number) => (event: React.PointerEvent<HTMLButtonElement>) => {
    const pointerState = pointerStateRef.current;
    if (!pointerState || pointerState.id !== emailId) return;

    const deltaX = event.clientX - pointerState.startX;
    const deltaY = event.clientY - pointerState.startY;
    if (Math.abs(deltaX) <= Math.abs(deltaY) || Math.abs(deltaX) < 12) return;

    if (capturedPointerIdsRef.current[emailId] !== event.pointerId) {
      event.currentTarget.setPointerCapture(event.pointerId);
      capturedPointerIdsRef.current[emailId] = event.pointerId;
    }

    const nextOffset = Math.max(-108, Math.min(108, deltaX));
    swipeOffsetsRef.current[emailId] = nextOffset;

    setSwipeOffsets((prev) => ({
      ...prev,
      [emailId]: nextOffset,
    }));
  };

  const handlePointerEnd = (email: EmailItem) => async (event: React.PointerEvent<HTMLButtonElement>) => {
    const currentTarget = event.currentTarget;
    const offset = swipeOffsetsRef.current[email.id] || 0;

    if (offset > 84) {
      await handleQueueEmail(email);
    } else if (offset < -84) {
      await handleCompleteEmail(email);
    }

    setSwipeOffsets((prev) => ({
      ...prev,
      [email.id]: 0,
    }));
    swipeOffsetsRef.current[email.id] = 0;
    pointerStateRef.current = null;
    if (capturedPointerIdsRef.current[email.id] === event.pointerId && (typeof currentTarget.hasPointerCapture !== 'function' || currentTarget.hasPointerCapture(event.pointerId))) {
      currentTarget.releasePointerCapture(event.pointerId);
    }
    delete capturedPointerIdsRef.current[email.id];
  };

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
            <div className="mt-3 flex flex-wrap gap-2 text-[11px] font-bold">
              <span className="inline-flex items-center gap-1 rounded-full border border-primary/15 bg-primary/10 px-2.5 py-1 text-primary">
                <Network className="size-3" aria-hidden="true" />
                맥락 종합
              </span>
              <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/15 bg-emerald-500/10 px-2.5 py-1 text-emerald-700">
                <CheckCircle2 className="size-3" aria-hidden="true" />
                실행 항목
              </span>
            </div>
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
        {mailboxAccounts.length > 0 ? (
          <div className="mt-3">
            <label htmlFor="mailbox-account-filter" className="sr-only">Mailbox account filter</label>
            <select
              id="mailbox-account-filter"
              aria-label="Mailbox account filter"
              value={selectedMailboxAccountId ?? ''}
              onChange={(event) => {
                const value = event.target.value ? Number(event.target.value) : null;
                setSelectedMailboxAccountId(value);
                void fetchEmails(searchQuery, value);
              }}
              className="flex h-10 w-full rounded-xl border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="">전체 계정</option>
              {mailboxAccounts.map((account) => (
                <option key={account.id} value={account.id}>{account.display_name || account.email_address}</option>
              ))}
            </select>
          </div>
        ) : null}
      </div>
      <ScrollArea className="min-h-0 flex-1 w-full">
        <div className="flex flex-col gap-2 p-3">
          {queueFeedback ? (
            <div role="status" aria-live="polite" className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3 text-sm font-semibold text-emerald-700">
              {queueFeedback}
            </div>
          ) : null}
          {loading ? (
            <div role="status" aria-live="polite" className="rounded-2xl border border-border bg-background/70 p-4 text-sm text-muted-foreground">메일을 불러오는 중입니다...</div>
          ) : error ? (
            <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">{error}</div>
          ) : emails.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border bg-background/70 p-5 text-sm text-muted-foreground">
              <p className="font-bold text-foreground">검색 결과가 없습니다</p>
              <p className="mt-1 text-xs leading-5">검색어를 바꾸거나 메일 동기화 상태를 확인하세요.</p>
            </div>
          ) : (
            emails.map((email: EmailItem) => {
              const selected = selectedEmailId === email.id;

              return (
                <div key={email.id} className="relative overflow-hidden rounded-2xl border border-border bg-background/60">
                  <div className="pointer-events-none absolute inset-0 flex items-center justify-between px-4 text-[11px] font-black uppercase tracking-[0.16em] text-muted-foreground">
                    <span className="inline-flex items-center gap-1 text-emerald-700"><ChevronRight className="size-3.5" /> 실행 목록</span>
                    <span className="inline-flex items-center gap-1 text-slate-500">완료 처리 <ChevronLeft className="size-3.5" /></span>
                  </div>
                  <button
                    onClick={() => {
                      if (suppressSelectionRef.current === email.id) {
                        suppressSelectionRef.current = null;
                        return;
                      }
                      onSelectEmail(email.id, email, selectedMailboxAccountId);
                    }}
                    onPointerDown={handlePointerDown(email.id)}
                    onPointerMove={handlePointerMove(email.id)}
                    onPointerUp={handlePointerEnd(email)}
                    onPointerCancel={handlePointerEnd(email)}
                    aria-current={selected ? "true" : undefined}
                    aria-label={`${email.subject || '(제목 없음)'} 메일. 오른쪽으로 밀면 실행 목록에 담고, 왼쪽으로 밀면 완료 처리합니다.`}
                    style={{ transform: `translateX(${swipeOffsets[email.id] || 0}px)`, touchAction: 'pan-y' }}
                    data-swipe-email-id={email.id}
                    className={`group relative flex min-h-20 w-full flex-col items-start gap-2 overflow-hidden rounded-2xl border p-3 pl-4 text-left text-sm transition-transform duration-150 ease-out hover:border-primary/35 hover:bg-primary/5 hover:shadow-md focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${selected ? 'border-primary/60 bg-primary/10 shadow-[0_16px_36px_rgba(37,99,255,0.14)]' : 'border-border bg-card'}`}
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
                        <div className="truncate text-sm font-bold flex-1 text-foreground">{email.subject || '(제목 없음)'}</div>
                        {mailboxAccountLabel(email.mailbox_account_id) ? (
                          <Badge variant="outline" className="h-5 whitespace-nowrap px-2 py-0 text-[10px] leading-none">
                            {mailboxAccountLabel(email.mailbox_account_id)}
                          </Badge>
                        ) : null}
                        {selectedMailboxAccountId && email.mailbox_account_id == null ? (
                          <Badge variant="outline" className="h-5 whitespace-nowrap border-amber-500/25 bg-amber-500/10 px-2 py-0 text-[10px] leading-none text-amber-700">
                            이전 복원 메일
                          </Badge>
                        ) : null}
                        {email.reply_count && email.reply_count > 1 && (
                          <Badge variant="secondary" className="h-5 whitespace-nowrap border border-primary/10 bg-primary/10 px-2 py-0 text-[10px] leading-none text-primary flex items-center gap-1">
                            <MessagesSquare className="w-3 h-3" />
                            {email.reply_count}개 메시지
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="line-clamp-2 w-full text-xs leading-5 text-muted-foreground">
                      {email.snippet}
                    </div>
                    {email.unread && (
                      <div className="flex items-center gap-2">
                        <Badge variant="default" className="bg-emerald-500 text-[10px] text-white">새 메일</Badge>
                      </div>
                    )}
                  </button>
                  <div className="relative z-10 grid grid-cols-2 gap-2 border-t border-border/70 bg-card/95 p-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      aria-label={`${email.subject || '(제목 없음)'} 메일을 실행 목록에 담기`}
                      className="h-9 rounded-xl text-xs font-bold"
                      onClick={() => void handleQueueEmail(email)}
                    >
                      실행 목록에 추가
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      aria-label={`${email.subject || '(제목 없음)'} 실행 항목 완료 처리`}
                      className="h-9 rounded-xl text-xs font-bold"
                      onClick={() => void handleCompleteEmail(email)}
                    >
                      완료 처리
                    </Button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
