import React, { useEffect, useState } from 'react';
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";

interface EmailData {
  id: number;
  subject: string | null;
  sender: string;
  body: string;
  date: string;
  thread_id?: string;
}

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

  const [draft, setDraft] = useState<string>('');
  const [isDrafting, setIsDrafting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  
  const [draftError, setDraftError] = useState<string | null>(null);
  const [sendStatus, setSendStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const [instruction, setInstruction] = useState('reply politely');

  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);

  useEffect(() => {
    if (!emailId) return;
    
    let isMounted = true;

    const fetchData = async () => {
      setLoading(true);
      setEmail(null);
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
            }
          } catch (err) {
            console.error("Error fetching thread:", err);
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
  }, [emailId]);

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
        body: JSON.stringify({
          to: email.sender,
          subject: email.subject?.startsWith('Re:') ? email.subject : `Re: ${email.subject || ''}`,
          body: draft
        })
      });
      if (!res.ok) throw new Error("Failed to send email");
      setSendStatus({ type: 'success', message: 'Reply sent successfully!' });
      setDraft('');
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
    } catch (err) {
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
    return <div className="flex items-center justify-center h-full text-muted-foreground">Loading details...</div>;
  }

  if (!email) {
    return <div className="flex items-center justify-center h-full text-muted-foreground text-red-500">Error loading email</div>;
  }

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
              Reply-To: {email.sender}
            </div>
          </div>
          <div className="text-xs text-muted-foreground whitespace-nowrap">
            {new Date(email.date).toLocaleString()}
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
                      <Checkbox className="mt-1" />
                      <span className="font-medium">{todo}</span>
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
              <Badge variant="secondary" className="text-[10px]">{threadEmails.length > 0 ? threadEmails.length : 1} msgs</Badge>
            </div>
            <div className="space-y-4">
              {(threadEmails.length > 0 ? threadEmails : [email]).map((msg) => (
                <div key={msg.id} className="rounded-lg border p-4 bg-card text-card-foreground">
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
            <div className="flex flex-col sm:flex-row sm:items-end gap-2 justify-between">
              <div className="space-y-1.5 flex-1 max-w-sm">
                <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">Reply</h3>
                <Input
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
            
            {draftError && <p className="text-sm text-red-500">{draftError}</p>}

            <Textarea 
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Your reply..."
              className="min-h-[150px]"
            />
            
            <div className="flex items-center justify-between">
              <div>
                {sendStatus && (
                  <p className={`text-sm ${sendStatus.type === 'success' ? 'text-green-600' : 'text-red-500'}`}>
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