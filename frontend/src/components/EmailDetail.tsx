import React, { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { MessagesSquare } from "lucide-react";
import {
  buildThreadUrl,
  buildReplyPayload,
  formatEmailDate,
  getConversationMessages,
  type ThreadEmailData,
} from "@/lib/email-threading";

type EmailData = ThreadEmailData;

interface LlmData {
  summary: string;
  todos: string[];
}

export function EmailDetail({ emailId, mailboxAccountId }: { emailId: number | null; mailboxAccountId?: number | null }) {
  const [email, setEmail] = useState<EmailData | null>(null);
  const [threadEmails, setThreadEmails] = useState<EmailData[]>([]);
  const [llmData, setLlmData] = useState<LlmData | null>(null);
  const [llmError, setLlmError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [threadLoading, setThreadLoading] = useState(false);
  const [threadError, setThreadError] = useState<string | null>(null);

  const [draft, setDraft] = useState<string>('');
  const [isDrafting, setIsDrafting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  
  const [draftError, setDraftError] = useState<string | null>(null);
  const [sendStatus, setSendStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const [instruction, setInstruction] = useState('정중하게 답장해줘');

  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const threadRequestIdRef = useRef(0);

  const fetchThread = useCallback(async (currentEmail: EmailData) => {
    const requestId = threadRequestIdRef.current + 1;
    threadRequestIdRef.current = requestId;
    const isLatestThreadRequest = () => requestId === threadRequestIdRef.current;

    setThreadError(null);

    if (!currentEmail.thread_id) {
      if (isLatestThreadRequest()) {
        setThreadLoading(false);
        setThreadEmails([currentEmail]);
      }
      return;
    }

    setThreadLoading(true);
    try {
      const threadJson = await apiClient.get<{ thread: EmailData[] }>(
        buildThreadUrl('', currentEmail.thread_id, currentEmail.mailbox_account_id ?? mailboxAccountId),
      );
      if (!isLatestThreadRequest()) return;
      setThreadEmails(threadJson.thread || []);
    } catch (err) {
      if (!isLatestThreadRequest()) return;
      console.error("Error fetching thread:", err);
      setThreadError("대화 흐름을 불러오지 못했습니다.");
      setThreadEmails([currentEmail]);
    } finally {
      if (isLatestThreadRequest()) setThreadLoading(false);
    }
  }, [mailboxAccountId]);

  useEffect(() => {
    if (!emailId) return;
    
    let isMounted = true;

    const fetchData = async () => {
      threadRequestIdRef.current += 1;
      setLoading(true);
      setEmail(null);
      setThreadEmails([]);
      setThreadError(null);
      setDetailError(null);
      setLlmData(null);
      setLlmError(null);
      setDraft('');
      setDraftError(null);
      setSendStatus(null);

      try {
        const emailJson = await apiClient.get<EmailData>(`/api/emails/${emailId}`);
        
        if (!isMounted) return;
        setEmail(emailJson);

        await fetchThread(emailJson);

        try {
          const llmJson = await apiClient.post<LlmData>('/api/llm/summarize', { email_body: emailJson.body });
          if (!isMounted) return;
          setLlmData(llmJson);
        } catch (llmErr) {
          console.error("Error generating LLM summary:", llmErr);
          if (isMounted) setLlmError("요약을 생성하지 못했습니다.");
        }
      } catch (err) {
        console.error("Error fetching email details:", err);
        if (isMounted) setDetailError("메일 내용을 불러오지 못했습니다.");
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchData();

    return () => { isMounted = false; };
  }, [emailId, fetchThread]);

  const handleDraftReply = async () => {
    if (!email) return;
    setIsDrafting(true);
    setDraftError(null);
    setSendStatus(null);
    try {
      const data = await apiClient.post<{ draft: string }>('/api/llm/draft', { email_body: email.body, instruction });
      setDraft(data.draft || '');
    } catch (err) {
      console.error("Error drafting reply:", err);
      setDraftError("답장 초안을 생성하지 못했습니다.");
    } finally {
      setIsDrafting(false);
    }
  };

  const handleSendReply = async () => {
    if (!email || !draft) return;
    setIsSending(true);
    setSendStatus(null);
    try {
      const data = await apiClient.post<{ simulated: boolean }>('/api/emails/send', buildReplyPayload(email, draft));
      setSendStatus({
        type: 'success',
        message: data.simulated
          ? '개발 모드에서 답장을 시뮬레이션했습니다. 실제 이메일은 전송되지 않았습니다.'
          : '답장을 전송했습니다.',
      });
      setDraft('');
      await fetchThread(email);
    } catch (err) {
      console.error("Error sending email:", err);
      setSendStatus({ type: 'error', message: '답장 전송에 실패했습니다.' });
    } finally {
      setIsSending(false);
    }
  };

  const handleSyncCalendar = async () => {
    if (!llmData || !llmData.todos.length) return;
    setIsSyncing(true);
    setSyncStatus(null);
    try {
      const data = await apiClient.post<{ synced: number }>('/api/calendar/sync', { todos: llmData.todos });
      setSyncStatus({ type: 'success', message: `${data.synced}개 일정이 캘린더에 반영되었습니다.` });
    } catch {
      setSyncStatus({ type: 'error', message: '캘린더 반영에 실패했습니다.' });
    } finally {
      setIsSyncing(false);
    }
  };

  if (!emailId) {
    return (
      <div className="flex h-full items-center justify-center bg-gradient-to-br from-card via-background to-primary/5 p-8 text-center text-muted-foreground">
        <div className="max-w-md rounded-3xl border border-primary/15 bg-card p-8 shadow-[0_24px_70px_rgba(15,23,42,0.08)]">
          <div className="mx-auto mb-4 grid size-14 place-items-center rounded-2xl bg-primary/10 text-2xl" aria-hidden="true">✦</div>
          <h2 className="text-xl font-black tracking-tight text-foreground">메일을 선택하세요</h2>
          <p className="mt-2 text-sm leading-6">왼쪽 받은편지함에서 메일을 선택하면 Naruon이 요약, 판단 포인트, 실행 항목을 연결합니다.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return <div role="status" aria-live="polite" className="flex h-full items-center justify-center bg-card text-muted-foreground">메일 내용을 불러오는 중입니다...</div>;
  }

  if (!email || detailError) {
    return <div role="alert" className="flex h-full items-center justify-center bg-card text-red-500">{detailError || '메일 내용을 불러오지 못했습니다.'}</div>;
  }

  const conversationMessages = getConversationMessages(email, threadEmails);

  return (
    <div className="flex h-full flex-col bg-card">
      <div className="flex items-start bg-gradient-to-br from-card via-card to-primary/5 p-6">
        <div className="flex w-full items-start gap-4 text-sm">
          <Avatar className="h-11 w-11 border border-primary/10 bg-primary/10 text-primary shadow-sm">
            <AvatarFallback>{email.sender ? email.sender.charAt(0).toUpperCase() : 'U'}</AvatarFallback>
          </Avatar>
          <div className="grid min-w-0 flex-1 gap-1">
            <div className="break-words text-lg font-black tracking-tight text-foreground xl:text-xl">{email.subject || '(제목 없음)'}</div>
            <div className="line-clamp-1 text-xs">
              <span className="text-muted-foreground">{email.sender}</span>
            </div>
            <div className="line-clamp-1 text-xs text-muted-foreground">
              답장 주소: {email.reply_to || email.sender}
            </div>
          </div>
          <div className="hidden whitespace-nowrap rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm 2xl:block">
            {formatEmailDate(email.date)}
          </div>
        </div>
      </div>
      <Separator />
      <ScrollArea className="min-h-0 flex-1">
        <div className="flex flex-col gap-6 bg-background/50 p-6">
          
          <div className="space-y-2 rounded-2xl border border-primary/20 bg-card p-4 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="grid size-8 place-items-center rounded-xl bg-primary/10 text-primary" aria-hidden="true">✦</span>
              <h3 className="text-sm font-black text-primary">맥락 종합</h3>
              <Badge variant="secondary" className="border border-primary/10 bg-primary/10 text-[10px] text-primary">AI 생성</Badge>
            </div>
            <div className="rounded-xl bg-primary/5 p-4 text-sm leading-6">
              {llmData ? (
                <p className="text-sm">{llmData.summary}</p>
              ) : llmError ? (
                <p className="text-sm text-red-500">{llmError}</p>
              ) : (
                <p className="text-sm text-muted-foreground italic">요약을 생성하는 중입니다...</p>
              )}
            </div>
          </div>

          <div className="space-y-2 rounded-2xl border border-emerald-500/20 bg-card p-4 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="grid size-8 place-items-center rounded-xl bg-emerald-500/10 text-emerald-600" aria-hidden="true">✓</span>
              <h3 className="text-sm font-black text-emerald-700">실행 항목</h3>
              <Badge variant="secondary" className="border border-emerald-500/10 bg-emerald-500/10 text-[10px] text-emerald-700">{llmData?.todos.length || 0}개 실행 항목</Badge>
            </div>
            {llmData ? (
              llmData.todos.length > 0 ? (
                <ul className="list-none space-y-2 text-sm">
                  {llmData.todos.map((todo, idx) => (
                    <li key={idx} className="flex items-start gap-3 rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-3">
                      <Checkbox id={`todo-${idx}`} className="mt-1" />
                      <label htmlFor={`todo-${idx}`} className="font-semibold leading-5 text-foreground">{todo}</label>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">실행 항목이 없습니다.</p>
              )
            ) : llmError ? (
              <p className="text-sm text-red-500">실행 항목을 추출하지 못했습니다.</p>
            ) : (
              <p className="text-sm text-muted-foreground italic">실행 항목을 추출하는 중입니다...</p>
            )}
            
            {llmData && llmData.todos.length > 0 && (
              <div className="mt-4 flex items-center justify-between">
                <Button 
                  size="sm" 
                  onClick={handleSyncCalendar} 
                  disabled={isSyncing}
                  className="h-9 rounded-xl bg-emerald-600 px-4 text-white hover:bg-emerald-700"
                >
                  {isSyncing ? "동기화 중" : "캘린더 반영"}
                </Button>
                {syncStatus && (
                  <span className={`text-xs ${syncStatus.type === 'success' ? 'text-green-600' : 'text-red-500'}`}>
                    {syncStatus.message}
                  </span>
                )}
              </div>
            )}
          </div>

          <Separator />
          
          <div className="space-y-4 rounded-2xl border border-border bg-card p-4 shadow-sm">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-black text-foreground">대화 흐름</h3>
              <Badge variant="secondary" className="text-[10px] flex items-center gap-1 border border-primary/10 bg-primary/10 text-primary">
                <MessagesSquare className="w-3 h-3" />
                {conversationMessages.length}개 메시지
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">오래된 메시지부터 최신 메시지 순서로 보여줍니다. 답장은 선택된 메시지를 기준으로 작성됩니다.</p>
            {threadLoading && <p role="status" aria-live="polite" className="text-sm text-muted-foreground">대화 흐름을 불러오는 중입니다...</p>}
            {threadError && (
              <div role="alert" className="flex items-center gap-3 text-sm text-red-500">
                <span>{threadError}</span>
                <Button size="sm" variant="outline" onClick={() => fetchThread(email)}>다시 시도</Button>
              </div>
            )}
            <div className="space-y-4">
              {conversationMessages.map((msg) => (
                <div key={msg.id} className={`rounded-2xl border p-4 text-card-foreground ${msg.id === email.id ? 'border-primary/60 bg-primary/5 shadow-sm' : 'border-border bg-background/60'}`} aria-current={msg.id === email.id ? "true" : undefined}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{msg.sender}</span>
                    <span className="text-xs text-muted-foreground">{formatEmailDate(msg.date)}</span>
                  </div>
                  {msg.id === email.id && <Badge variant="outline" className="mb-2 border-primary/30 text-[10px] text-primary">선택된 메시지</Badge>}
                  <div className="text-sm leading-6 whitespace-pre-wrap">{msg.body}</div>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          <div className="space-y-4 rounded-2xl border border-purple-500/20 bg-card p-4 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-end gap-2 justify-between">
              <div className="space-y-1.5 flex-1 max-w-sm">
                <h3 className="text-sm font-black text-purple-700">답장 실행</h3>
                <label htmlFor="reply-instruction" className="sr-only">AI 답장 지시</label>
                <Input
                  id="reply-instruction"
                  aria-label="AI 답장 지시"
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  placeholder="예: 정중하게 답장해줘"
                  className="h-10 rounded-xl border-purple-500/20 bg-purple-500/5 text-xs"
                />
              </div>
              <Button 
                onClick={handleDraftReply} 
                disabled={isDrafting || !instruction}
                variant="outline"
                size="sm"
                className="h-10 rounded-xl border-purple-500/30 px-4 text-purple-700 hover:bg-purple-500/10"
              >
                {isDrafting ? "초안 작성 중" : "AI 답장 초안"}
              </Button>
            </div>
            
            {draftError && <p role="alert" className="text-sm text-red-500">{draftError}</p>}

            <label htmlFor="reply-draft" className="sr-only">답장 초안</label>
            <Textarea 
              id="reply-draft"
              aria-label="답장 초안"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="답장 초안을 작성하거나 AI 초안을 생성하세요..."
              className="min-h-[150px] rounded-2xl border-purple-500/20 bg-background/70"
            />
            
            <div className="flex items-center justify-between">
              <div>
                {sendStatus && (
                  <p role={sendStatus.type === 'error' ? 'alert' : 'status'} aria-live="polite" className={`text-sm ${sendStatus.type === 'success' ? 'text-green-600' : 'text-red-500'}`}>
                    {sendStatus.message}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                {draft && (
                  <Button 
                    onClick={() => { setDraft(''); setSendStatus(null); setDraftError(null); }} 
                    variant="ghost"
                    size="sm"
                    className="h-9 rounded-xl"
                  >
                    지우기
                  </Button>
                )}
                <Button 
                  onClick={handleSendReply} 
                  disabled={isSending || !draft}
                  size="sm"
                  className="h-9 rounded-xl px-4"
                >
                  {isSending ? "전송 중" : "답장 보내기"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
