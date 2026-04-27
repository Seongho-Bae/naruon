import React, { useEffect, useState } from 'react';
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface EmailData {
  id: number;
  subject: string | null;
  sender: string;
  body: string;
  date: string;
}

interface LlmData {
  summary: string;
  todos: string[];
}

export function EmailDetail({ emailId }: { emailId: number | null }) {
  const [email, setEmail] = useState<EmailData | null>(null);
  const [llmData, setLlmData] = useState<LlmData | null>(null);
  const [llmError, setLlmError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [draft, setDraft] = useState<string>('');
  const [isDrafting, setIsDrafting] = useState(false);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    if (!emailId) return;
    
    let isMounted = true;

    const fetchData = async () => {
      setLoading(true);
      setEmail(null);
      setLlmData(null);
      setLlmError(null);
      setDraft('');

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const emailRes = await fetch(`${apiUrl}/api/emails/${emailId}`);
        if (!emailRes.ok) throw new Error("Failed to fetch email details");
        const emailJson = await emailRes.json();
        
        if (!isMounted) return;
        setEmail(emailJson);

        try {
          const llmRes = await fetch(`${apiUrl}/api/llm/summarize`, {
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
    setDraft('');
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/llm/draft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_body: email.body, instruction: 'reply politely' })
      });
      if (!res.ok) throw new Error("Failed to generate draft");
      const data = await res.json();
      setDraft(data.draft || '');
    } catch (err) {
      console.error("Error drafting reply:", err);
      setDraft("Error generating draft.");
    } finally {
      setIsDrafting(false);
    }
  };

  const handleSendReply = async () => {
    if (!email || !draft) return;
    setIsSending(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/emails/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to: email.sender,
          subject: email.subject?.startsWith('Re:') ? email.subject : `Re: ${email.subject || ''}`,
          body: draft
        })
      });
      if (!res.ok) throw new Error("Failed to send email");
      alert("Reply sent successfully!");
      setDraft('');
    } catch (err) {
      console.error("Error sending email:", err);
      alert("Error sending reply.");
    } finally {
      setIsSending(false);
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
          </div>

          <Separator />
          
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase text-muted-foreground tracking-wider">Original Message</h3>
            <div className="text-sm whitespace-pre-wrap">
              {email.body}
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-primary uppercase tracking-wider">Reply</h3>
              <Button 
                onClick={handleDraftReply} 
                disabled={isDrafting}
                variant="outline"
                size="sm"
              >
                {isDrafting ? "Drafting..." : "Draft Reply with AI"}
              </Button>
            </div>
            
            <Textarea 
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Your reply..."
              className="min-h-[150px]"
            />
            
            <div className="flex justify-end">
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
      </ScrollArea>
    </div>
  );
}