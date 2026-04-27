import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

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
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!emailId) return;
    
    let isMounted = true;

    const fetchData = async () => {
      setLoading(true);
      setEmail(null);
      setLlmData(null);

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const emailRes = await fetch(`${apiUrl}/api/emails/${emailId}`);
        if (!emailRes.ok) throw new Error("Failed to fetch email details");
        const emailJson = await emailRes.json();
        
        if (!isMounted) return;
        setEmail(emailJson);

        const llmRes = await fetch(`${apiUrl}/api/llm/summarize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email_body: emailJson.body })
        });
        if (!llmRes.ok) throw new Error("Failed to generate summary");
        const llmJson = await llmRes.json();
        
        if (!isMounted) return;
        setLlmData(llmJson);
      } catch (err) {
        console.error("Error fetching email details:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchData();

    return () => { isMounted = false; };
  }, [emailId]);

  if (!emailId) {
    return <div className="flex items-center justify-center h-full text-muted-foreground">Select an email to view details</div>;
  }

  if (loading) {
    return <div className="flex items-center justify-center h-full text-muted-foreground">Loading details...</div>;
  }

  if (!email) {
    return <div className="flex items-center justify-center h-full text-muted-foreground text-red-500">Error loading email</div>;
  }

  return (
    <div className="p-6 h-full flex flex-col gap-6 overflow-y-auto">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">{email.subject || '(No Subject)'}</h2>
        <p className="text-muted-foreground">{email.sender} - {new Date(email.date).toLocaleString()}</p>
      </div>
      <Separator />
      
      {/* Actual Body */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Original Content</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="whitespace-pre-wrap text-sm text-muted-foreground overflow-x-auto max-h-64 overflow-y-auto">
            {email.body}
          </div>
        </CardContent>
      </Card>
      
      {/* AI Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">AI Summary</CardTitle>
        </CardHeader>
        <CardContent>
          {llmData ? (
            <p className="text-sm">{llmData.summary}</p>
          ) : (
            <p className="text-sm text-muted-foreground italic">Generating summary...</p>
          )}
        </CardContent>
      </Card>
      
      {/* AI TODOs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Extracted TODOs</CardTitle>
        </CardHeader>
        <CardContent>
          {llmData ? (
            llmData.todos.length > 0 ? (
              <ul className="list-disc pl-5 text-sm space-y-1">
                {llmData.todos.map((todo, idx) => <li key={idx}>{todo}</li>)}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No TODOs found.</p>
            )
          ) : (
            <p className="text-sm text-muted-foreground italic">Extracting TODOs...</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
