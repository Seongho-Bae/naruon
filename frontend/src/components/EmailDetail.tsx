import React, { useCallback, useEffect, useRef, useState } from 'react';
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

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function EmailDetail({ emailId }: { emailId: number | null }) {
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
  const [instruction, setInstruction] = useState('reply politely');

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
      const threadRes = await fetch(buildThreadUrl(API_URL, currentEmail.thread_id));
      if (!threadRes.ok) throw new Error("Failed to fetch thread");
      const threadJson = await threadRes.json();
      if (!isLatestThreadRequest()) return;
      setThreadEmails(threadJson.thread || []);
    } catch (err) {
      if (!isLatestThreadRequest()) return;
      console.error("Error fetching thread:", err);
      setThreadError("Conversation could not load.");
      setThreadEmails([currentEmail]);
    } finally {
      if (isLatestThreadRequest()) setThreadLoading(false);
    }
  }, []);

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
        const emailRes = await fetch(`${API_URL}/api/emails/${emailId}`);
        if (!emailRes.ok) throw new Error("Failed to fetch email details");
        const emailJson = await emailRes.json();
        
        if (!isMounted) return;
        setEmail(emailJson);

        await fetchThread(emailJson);

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
        if (isMounted) setDetailError("Error loading email");
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
      setDraftError("Error generating draft.");
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
        body: JSON.stringify(buildReplyPayload(email, draft))
      });
      if (!res.ok) throw new Error("Failed to send email");
      const result = await res.json();
      setSendStatus({
        type: 'success',
        message: result.simulated
          ? 'Reply simulated in development mode. No email was delivered.'
          : 'Reply sent successfully!',
      });
      setDraft('');
      await fetchThread(email);
    } catch (err) {
      console.error("Error sending email:", err);
      setSendStatus({ type: 'error', message: 'Error sending reply.' });
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
      setSyncStatus({ type: 'success', message: `Synced ${data.synced} events!` });
    } catch {
      setSyncStatus({ type: 'error', message: 'Error syncing to calendar.' });
    } finally {
      setIsSyncing(false);
    }
  };

  if (!emailId) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-muted-foreground">
        <div className="max-w-sm">
          <h2 className="text-lg font-medium text-foreground">No email selected</h2>
          <p className="text-sm">Select an email from the list on the left to view its details, summary, and extracted tasks.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return <div role="status" aria-live="polite" className="flex items-center justify-center h-full text-muted-foreground">Loading details...</div>;
  }

  if (!email || detailError) {
    return <div role="alert" className="flex items-center justify-center h-full text-muted-foreground text-red-500">{detailError || 'Error loading email'}</div>;
  }

  const conversationMessages = getConversationMessages(email, threadEmails);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-start p-6">
        <div className="flex items-start gap-4 text-sm w-full">
          <Avatar className="h-10 w-10">
            <AvatarFallback>{email.sender ? email.sender.charAt(0).toUpperCase() : 'U'}</AvatarFallback>
          </Avatar>
          <div className="grid gap-1 flex-1">
            <div className="font-semibold text-base">{email.subject || '(No Subject)'}</div>
            <div className="line-clamp-1 text-xs">
              <span className="text-muted-foreground">{email.sender}</span>
            </div>
            <div className="line-clamp-1 text-xs text-muted-foreground">
              Reply-To: {email.reply_to || email.sender}
            </div>
          </div>
          <div className="text-xs text-muted-foreground whitespace-nowrap">
            {formatEmailDate(email.date)}
          </div>
        </div>
      </div>
      <Separator />
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-6 p-6">
          
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">AI Summary</h3>
              <Badge variant="secondary" className="text-[10px]">Generated</Badge>
            </div>
            <div className="rounded-md bg-muted/50 p-4 text-sm">
              {llmData ? (
                <p className="text-sm">{llmData.summary}</p>
              ) : llmError ? (
                <p className="text-sm text-red-500">{llmError}</p>
              ) : (
                <p className="text-sm text-muted-foreground italic">Generating summary...</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">Extracted Action Items</h3>
              <Badge variant="secondary" className="text-[10px]">{llmData?.todos.length || 0} Tasks</Badge>
            </div>
            {llmData ? (
              llmData.todos.length > 0 ? (
                <ul className="list-none space-y-2 text-sm">
                  {llmData.todos.map((todo, idx) => (
                    <li key={idx} className="flex items-start gap-2 rounded-md border p-3">
                      <Checkbox id={`todo-${idx}`} className="mt-1" />
                      <label htmlFor={`todo-${idx}`} className="font-medium">{todo}</label>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No action items found.</p>
              )
            ) : llmError ? (
              <p className="text-sm text-red-500">Failed to extract action items</p>
            ) : (
              <p className="text-sm text-muted-foreground italic">Extracting action items...</p>
            )}
            
            {llmData && llmData.todos.length > 0 && (
              <div className="mt-4 flex items-center justify-between">
                <Button 
                  size="sm" 
                  onClick={handleSyncCalendar} 
                  disabled={isSyncing}
                >
                  {isSyncing ? "Syncing..." : "Sync to Calendar"}
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
          
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold uppercase text-muted-foreground tracking-wider">Conversation History</h3>
              <Badge variant="secondary" className="text-[10px] flex items-center gap-1">
                <MessagesSquare className="w-3 h-3" />
                {conversationMessages.length} msgs
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">Oldest to newest. Replies target the selected message.</p>
            {threadLoading && <p role="status" aria-live="polite" className="text-sm text-muted-foreground">Loading conversation...</p>}
            {threadError && (
              <div role="alert" className="flex items-center gap-3 text-sm text-red-500">
                <span>{threadError}</span>
                <Button size="sm" variant="outline" onClick={() => fetchThread(email)}>Retry</Button>
              </div>
            )}
            <div className="space-y-4">
              {conversationMessages.map((msg) => (
                <div key={msg.id} className={`rounded-lg border p-4 bg-card text-card-foreground ${msg.id === email.id ? 'border-primary' : ''}`} aria-current={msg.id === email.id ? "true" : undefined}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{msg.sender}</span>
                    <span className="text-xs text-muted-foreground">{formatEmailDate(msg.date)}</span>
                  </div>
                  {msg.id === email.id && <Badge variant="outline" className="mb-2 text-[10px]">Selected message</Badge>}
                  <div className="text-sm whitespace-pre-wrap">{msg.body}</div>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-end gap-2 justify-between">
              <div className="space-y-1.5 flex-1 max-w-sm">
                <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">Reply</h3>
                <label htmlFor="reply-instruction" className="sr-only">AI reply instruction</label>
                <Input
                  id="reply-instruction"
                  aria-label="AI reply instruction"
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  placeholder="e.g. reply politely"
                  className="h-8 text-xs"
                />
              </div>
              <Button 
                onClick={handleDraftReply} 
                disabled={isDrafting || !instruction}
                variant="outline"
                size="sm"
              >
                {isDrafting ? "Drafting..." : "Draft Reply with AI"}
              </Button>
            </div>
            
            {draftError && <p role="alert" className="text-sm text-red-500">{draftError}</p>}

            <label htmlFor="reply-draft" className="sr-only">Reply draft</label>
            <Textarea 
              id="reply-draft"
              aria-label="Reply draft"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Your reply..."
              className="min-h-[150px]"
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
                  >
                    Clear
                  </Button>
                )}
                <Button 
                  onClick={handleSendReply} 
                  disabled={isSending || !draft}
                  size="sm"
                >
                  {isSending ? "Sending..." : "Send Reply"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
