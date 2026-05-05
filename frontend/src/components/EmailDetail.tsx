import React, { useEffect, useState } from 'react';
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Archive, CalendarPlus, CheckCircle2, ClipboardList, FileText, Forward, MessageSquareReply, MessagesSquare, Network, RefreshCw, Reply, ReplyAll, ShieldAlert, Sparkles } from "lucide-react";

interface EmailData {
  id: number;
  subject: string | null;
  sender: string;
  body: string;
  date: string;
  thread_id?: string; // O3: email threading support
  message_id?: string;
  in_reply_to?: string;
  references?: string;
}

interface LlmData {
  summary: string;
  todos: string[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function EmailDetail({
  emailId,
  onOpenRelationshipContext,
}: {
  emailId: number | null;
  onOpenRelationshipContext?: () => void;
}) {
  const [email, setEmail] = useState<EmailData | null>(null);
  const [threadEmails, setThreadEmails] = useState<EmailData[]>([]);
  const [threadWarning, setThreadWarning] = useState<string | null>(null);
  const [llmData, setLlmData] = useState<LlmData | null>(null);
  const [llmError, setLlmError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  const [draft, setDraft] = useState<string>('');
  const [isDrafting, setIsDrafting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  
  const [draftError, setDraftError] = useState<string | null>(null);
  const [sendStatus, setSendStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const [instruction, setInstruction] = useState('정중하고 간결하게 답장');

  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);

  useEffect(() => {
    if (!emailId) return;
    
    let isMounted = true;

    const fetchData = async () => {
      setLoading(true);
      setEmail(null);
      setThreadEmails([]);
      setThreadWarning(null);
      setLlmData(null);
      setLlmError(null);
      setDraft('');
      setDraftError(null);
      setSendStatus(null);

      try {
        const emailRes = await fetch(`${API_URL}/api/emails/${emailId}`);
        if (!emailRes.ok) throw new Error("Failed to fetch email details");
        const emailJson = await emailRes.json();
        
        if (!isMounted) return;
        setEmail(emailJson);

        if (emailJson.thread_id) {
          try {
            const threadRes = await fetch(`${API_URL}/api/emails/thread/${emailJson.thread_id}`);
            if (threadRes.ok) {
              const threadJson = await threadRes.json();
              if (isMounted) setThreadEmails(threadJson.thread || []);
            } else if (isMounted) {
              setThreadWarning('스레드 전체를 불러오지 못해 선택한 메일만 표시합니다.');
              setThreadEmails([emailJson]);
            }
          } catch (err) {
            console.error("Error fetching thread:", err);
            if (isMounted) {
              setThreadWarning('스레드 전체를 불러오지 못해 선택한 메일만 표시합니다.');
              setThreadEmails([emailJson]);
            }
          }
        } else {
          if (isMounted) setThreadEmails([emailJson]);
        }

        try {
          const llmRes = await fetch(`${API_URL}/api/llm/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email_body: emailJson.body })
          });
          if (!llmRes.ok) throw new Error("Failed to generate summary");
          const llmJson = await llmRes.json();
          if (!isMounted) return;
          setLlmData(llmJson);
        } catch (llmErr) {
          console.error("Error generating LLM summary:", llmErr);
          if (isMounted) setLlmError("Failed to generate summary");
        }
      } catch (err) {
        console.error("Error fetching email details:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchData();

    return () => { isMounted = false; };
  }, [emailId, reloadToken]);

  const handleDraftReply = async () => {
    if (!email) return;
    setIsDrafting(true);
    setDraftError(null);
    setSendStatus(null);
    try {
      const res = await fetch(`${API_URL}/api/llm/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_body: email.body, instruction })
      });
      if (!res.ok) throw new Error("Failed to generate draft");
      const data = await res.json();
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
      const res = await fetch(`${API_URL}/api/emails/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: email.sender,
          subject: email.subject?.startsWith('Re:') ? email.subject : `Re: ${email.subject || ''}`,
          body: draft,
          in_reply_to: email.message_id,
          references: email.references ? `${email.references} ${email.message_id}` : email.message_id
        })
      });
      if (!res.ok) throw new Error("Failed to send email");
      setSendStatus({ type: 'success', message: '답장을 보냈습니다.' });
      setDraft('');
    } catch (err) {
      console.error("Error sending email:", err);
      setSendStatus({ type: 'error', message: '답장을 보내지 못했습니다.' });
    } finally {
      setIsSending(false);
    }
  };

  const handleSyncCalendar = async () => {
    if (!llmData || !llmData.todos.length) return;
    setIsSyncing(true);
    setSyncStatus(null);
    try {
      const res = await fetch(`${API_URL}/api/calendar/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          todos: llmData.todos,
          user_token: { token: 'mock' } // Mock token as required by API
        })
      });
      if (!res.ok) throw new Error("Failed to sync");
      const data = await res.json();
      setSyncStatus({ type: 'success', message: `${data.synced}개 일정을 반영했습니다.` });
    } catch {
      setSyncStatus({ type: 'error', message: '캘린더에 반영하지 못했습니다.' });
    } finally {
      setIsSyncing(false);
    }
  };

  if (!emailId) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-muted-foreground">
        <div className="max-w-sm rounded-3xl border border-dashed bg-card/80 p-8">
          <Sparkles className="mx-auto mb-4 size-9 text-primary" aria-hidden="true" />
          <h2 className="text-lg font-semibold text-foreground">메일을 선택하세요</h2>
          <p className="mt-2 text-sm">왼쪽 목록에서 메일을 고르면 요약, 실행 항목, 답장 초안을 함께 확인할 수 있습니다.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return <div role="status" aria-live="polite" className="flex h-full items-center justify-center text-muted-foreground"><RefreshCw className="mr-2 size-4 animate-spin" aria-hidden="true" />메일 맥락을 불러오는 중입니다...</div>;
  }

  if (!email) {
    return <div role="alert" className="flex h-full items-center justify-center text-destructive">메일 상세를 불러오지 못했습니다.</div>;
  }

  return (
    <div className="flex h-full flex-col bg-card">
      <div className="border-b bg-background/70 p-4 md:p-6">
        <div className="flex items-start gap-4 text-sm w-full">
          <Avatar className="h-10 w-10">
            <AvatarFallback>{email.sender ? email.sender.charAt(0).toUpperCase() : 'U'}</AvatarFallback>
          </Avatar>
          <div className="grid gap-1 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-black tracking-tight text-[#0B132B] md:text-2xl">{email.subject || '(제목 없음)'}</h1>
              <Badge variant="destructive" className="bg-red-50 text-red-600">중요</Badge>
              <Badge variant="secondary" className="text-primary">고객사</Badge>
            </div>
            <div className="line-clamp-1 text-xs">
              <span className="text-muted-foreground">{email.sender}</span>
            </div>
            <div className="line-clamp-1 text-xs text-muted-foreground">
              회신 주소: {email.sender}
            </div>
          </div>
          <div className="text-xs text-muted-foreground whitespace-nowrap">
            {new Date(email.date).toLocaleString()}
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2" aria-label="메일 빠른 작업">
          <Button type="button" variant="outline" className="h-10 rounded-xl"><Reply className="mr-1 size-4" aria-hidden="true" />답장</Button>
          <Button type="button" variant="outline" className="h-10 rounded-xl"><ReplyAll className="mr-1 size-4" aria-hidden="true" />전체답장</Button>
          <Button type="button" variant="outline" className="h-10 rounded-xl"><Forward className="mr-1 size-4" aria-hidden="true" />전달</Button>
          <Button type="button" variant="outline" className="h-10 rounded-xl"><CalendarPlus className="mr-1 size-4" aria-hidden="true" />일정 만들기</Button>
          <Button type="button" variant="outline" className="h-10 rounded-xl"><ClipboardList className="mr-1 size-4" aria-hidden="true" />작업 만들기</Button>
          <Button type="button" variant="outline" className="h-10 rounded-xl"><Archive className="mr-1 size-4" aria-hidden="true" />보관</Button>
          <Button type="button" className="h-10 rounded-xl" onClick={onOpenRelationshipContext}><Network className="mr-1 size-4" aria-hidden="true" />관계 그래프 보기</Button>
        </div>
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-6 p-6">
          
          <div className="naruon-ai-sheen space-y-3 rounded-2xl border border-primary/15 p-4">
            <div className="flex items-center gap-2">
              <Sparkles className="size-4 text-primary" aria-hidden="true" />
              <h3 className="text-sm font-semibold text-primary">AI 요약</h3>
              <Badge variant="secondary" className="text-[10px]">생성됨</Badge>
            </div>
            <p className="flex items-start gap-2 text-xs leading-5 text-muted-foreground">
              <ShieldAlert className="mt-0.5 size-3.5 shrink-0 text-primary" aria-hidden="true" />
              AI 요약은 원문을 기준으로 생성됩니다. 중요한 결정 전 원문을 확인하세요.
            </p>
            <div className="rounded-xl bg-white/70 p-4 text-sm leading-6 shadow-sm">
              {llmData ? (
                <p className="text-sm">{llmData.summary}</p>
              ) : llmError ? (
                <p role="alert" className="text-sm text-destructive">요약을 생성하지 못했습니다. 메일 본문은 계속 확인할 수 있습니다.</p>
              ) : (
                <p role="status" aria-live="polite" className="text-sm text-muted-foreground italic">AI가 메일 흐름을 요약하는 중입니다...</p>
              )}
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <div className="space-y-3 rounded-2xl border border-primary/15 bg-card p-4 shadow-sm">
              <div className="flex items-center gap-2">
                <Network className="size-4 text-primary" aria-hidden="true" />
                <h3 className="text-sm font-semibold">관계 맥락</h3>
                <Badge variant="secondary" className="text-[10px]">선택 메일 기준</Badge>
              </div>
              <p className="text-sm leading-6 text-muted-foreground">
                선택한 메일의 사람, 주제, 일정과 연결될 수 있는 관계 후보를 확인합니다. 그래프는 버튼을 눌렀을 때만 열립니다.
              </p>
              <Button type="button" variant="outline" className="h-10 rounded-xl" onClick={onOpenRelationshipContext}>
                <Network className="mr-1 size-4" aria-hidden="true" />관계 그래프 보기
              </Button>
            </div>
            <div className="space-y-3 rounded-2xl border bg-card p-4 shadow-sm">
              <div className="flex items-center gap-2">
                <CalendarPlus className="size-4 text-primary" aria-hidden="true" />
                <h3 className="text-sm font-semibold">관련 일정 후보</h3>
                <Badge variant="secondary" className="text-[10px]">AI</Badge>
              </div>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>고객사 미팅: 2024.05.29 14:00</li>
                <li>Q2 출시 내부 검토: 2024.06.10 15:00</li>
              </ul>
            </div>
          </div>

          <div className="space-y-3 rounded-2xl border bg-card p-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="size-4 text-[var(--success)]" aria-hidden="true" />
              <h3 className="text-sm font-semibold">실행 항목</h3>
              <Badge variant="secondary" className="text-[10px]">{llmData?.todos.length || 0}개</Badge>
            </div>
            {llmData ? (
              llmData.todos.length > 0 ? (
                <ul className="list-none space-y-2 text-sm">
                  {llmData.todos.map((todo, idx) => (
                    <li key={idx} className="flex items-start gap-2 rounded-xl border bg-muted/20 p-3">
                      <Checkbox className="mt-1" aria-label={`실행 항목 완료: ${todo}`} />
                      <span className="font-medium">{todo}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">이 메일에서 바로 실행할 항목을 찾지 못했습니다.</p>
              )
            ) : llmError ? (
              <p role="alert" className="text-sm text-destructive">실행 항목을 추출하지 못했습니다.</p>
            ) : (
              <p role="status" aria-live="polite" className="text-sm text-muted-foreground italic">실행 항목을 찾는 중입니다...</p>
            )}
            
            {llmData && llmData.todos.length > 0 && (
              <div className="mt-4 flex items-center justify-between">
                <Button 
                  size="sm" 
                  onClick={handleSyncCalendar} 
                  disabled={isSyncing}
                >
                  <CalendarPlus className="mr-1 size-3.5" aria-hidden="true" />
                  {isSyncing ? "반영 중" : "캘린더 반영"}
                </Button>
                {syncStatus && (
                  <span role={syncStatus.type === 'success' ? 'status' : 'alert'} className={`text-xs ${syncStatus.type === 'success' ? 'text-green-600' : 'text-red-500'}`}>
                    {syncStatus.message}
                  </span>
                )}
              </div>
            )}
          </div>

          <Separator />
          
          <div className="space-y-4">
            <div className="flex items-center gap-2">
                <FileText className="size-4 text-muted-foreground" aria-hidden="true" />
                <h3 className="text-sm font-semibold text-muted-foreground">대화 기록</h3>
              <Badge variant="secondary" className="text-[10px] flex items-center gap-1">
                <MessagesSquare className="w-3 h-3" />
                {threadEmails.length > 0 ? threadEmails.length : 1}개
              </Badge>
            </div>
            {threadWarning && (
              <div role="alert" className="flex flex-col gap-3 rounded-2xl border border-amber-300/60 bg-amber-50 p-4 text-sm text-amber-900 sm:flex-row sm:items-center sm:justify-between">
                <span>{threadWarning}</span>
                <Button type="button" variant="outline" size="sm" onClick={() => setReloadToken((value) => value + 1)}>
                  다시 시도
                </Button>
              </div>
            )}
            <div className="space-y-4">
              {(threadEmails.length > 0 ? threadEmails : [email]).map((msg) => (
                  <div key={msg.id} className="rounded-2xl border bg-background p-4 text-card-foreground">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{msg.sender}</span>
                    <span className="text-xs text-muted-foreground">{new Date(msg.date).toLocaleString()}</span>
                  </div>
                  <div className="text-sm whitespace-pre-wrap">{msg.body}</div>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="sr-only" role="status" aria-live="polite">
              {isDrafting ? '답장 초안을 생성하는 중입니다.' : isSending ? '답장을 전송하는 중입니다.' : ''}
            </div>
            <div className="flex flex-col sm:flex-row sm:items-end gap-2 justify-between">
              <div className="space-y-1.5 flex-1 max-w-sm">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-primary"><MessageSquareReply className="size-4" aria-hidden="true" />답장 초안</h3>
                <Input
                  aria-label="답장 작성 지시"
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  placeholder="예: 정중하고 짧게 답장"
                  className="h-8 text-xs"
                />
              </div>
              <Button 
                onClick={handleDraftReply} 
                disabled={isDrafting || !instruction}
                variant="outline"
                size="sm"
              >
                {isDrafting ? "작성 중" : "AI 답장 초안"}
              </Button>
            </div>
            
            {draftError && <p role="alert" className="text-sm text-red-500">{draftError}</p>}

            <Textarea 
              aria-label="답장 본문"
              value={draft}
                onChange={(e) => setDraft(e.target.value)}
              placeholder="답장 내용을 확인하고 수정하세요. 보내기는 사용자가 직접 눌러야 합니다."
              className="min-h-[150px]"
            />
            
            <div className="flex items-center justify-between">
              <div>
                {sendStatus && (
                  <p role={sendStatus.type === 'success' ? 'status' : 'alert'} className={`text-sm ${sendStatus.type === 'success' ? 'text-green-600' : 'text-red-500'}`}>
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
                  >
                    지우기
                  </Button>
                )}
                <Button 
                  onClick={handleSendReply} 
                  disabled={isSending || !draft}
                  size="sm"
                >
                  {isSending ? "전송 중" : "답장 보내기"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
      <div className="sticky bottom-0 grid grid-cols-4 gap-2 border-t bg-card/95 p-3 shadow-[0_-12px_30px_rgba(15,23,42,0.08)] md:hidden">
        <Button type="button" variant="outline" className="min-h-11 rounded-xl"><Reply className="mr-1 size-4" aria-hidden="true" />답장</Button>
        <Button type="button" variant="outline" className="min-h-11 rounded-xl"><ClipboardList className="mr-1 size-4" aria-hidden="true" />작업</Button>
        <Button type="button" variant="outline" className="min-h-11 rounded-xl"><CalendarPlus className="mr-1 size-4" aria-hidden="true" />일정</Button>
        <Button type="button" className="min-h-11 rounded-xl" onClick={onOpenRelationshipContext}><Network className="mr-1 size-4" aria-hidden="true" />맥락</Button>
      </div>
    </div>
  );
}
