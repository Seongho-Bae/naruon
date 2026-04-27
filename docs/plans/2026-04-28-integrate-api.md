# O4: Integrate Backend API into Email Dashboard UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate the backend API into the frontend Email Dashboard UI to fetch real email data, removing hardcoded dummy data.

**Architecture:** Create new `emails` endpoints in the FastAPI backend. Then update `EmailList` to fetch recent emails, and `EmailDetail` to fetch email details along with LLM-generated summaries and TODOs from the backend.

**Tech Stack:** FastAPI, React, Next.js, Tailwind CSS, shadcn/ui

---

### Task 1: Create Backend Emails API Endpoints

**Files:**
- Create: `backend/api/emails.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_emails_api.py`

**Step 1: Write the failing tests**

```python
# backend/tests/test_emails_api.py
import pytest
from httpx import AsyncClient
from db.models import Email

@pytest.mark.asyncio
async def test_get_emails(client: AsyncClient, db_session):
    response = await client.get("/api/emails?limit=10")
    assert response.status_code == 200
    assert "emails" in response.json()

@pytest.mark.asyncio
async def test_get_email_by_id(client: AsyncClient, db_session, sample_email: Email):
    response = await client.get(f"/api/emails/{sample_email.id}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_email.id
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_emails_api.py -v`
Expected: FAIL with 404 Not Found

**Step 3: Write minimal implementation**

Create `backend/api/emails.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models import Email
from pydantic import BaseModel
import datetime

router = APIRouter(prefix="/api/emails")

class EmailListItem(BaseModel):
    id: int
    subject: str | None
    sender: str
    date: datetime.datetime
    snippet: str

class EmailDetailResponse(BaseModel):
    id: int
    message_id: str
    sender: str
    recipients: str | None
    subject: str | None
    date: datetime.datetime
    body: str

@router.get("", response_model=dict[str, list[EmailListItem]])
async def get_emails(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Email).order_by(Email.date.desc()).limit(limit))
    emails = result.scalars().all()
    
    items = []
    for email in emails:
        snippet = email.body[:100] + "..." if len(email.body) > 100 else email.body
        items.append(EmailListItem(
            id=email.id,
            subject=email.subject,
            sender=email.sender,
            date=email.date,
            snippet=snippet
        ))
    return {"emails": items}

@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email(email_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Email).where(Email.id == email_id))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return EmailDetailResponse(
        id=email.id,
        message_id=email.message_id,
        sender=email.sender,
        recipients=email.recipients,
        subject=email.subject,
        date=email.date,
        body=email.body
    )
```

In `backend/main.py`:
```python
from api.emails import router as emails_router
...
app.include_router(emails_router)
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_emails_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/api/emails.py backend/main.py backend/tests/test_emails_api.py
git commit -m "feat: add emails API endpoints for dashboard"
```

### Task 2: Integrate Email List View

**Files:**
- Modify: `frontend/src/components/EmailList.tsx`

**Step 1: Write the minimal implementation**

Modify `frontend/src/components/EmailList.tsx` to fetch `/api/emails`:
```tsx
import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface EmailItem {
  id: number;
  subject: string | null;
  sender: string;
  date: string;
  snippet: string;
}

export function EmailList({ onSelectEmail }: { onSelectEmail: (id: number) => void }) {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/emails')
      .then(res => res.json())
      .then(data => {
        setEmails(data.emails || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching emails:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading emails...</div>;
  }

  return (
    <ScrollArea className="h-full w-full border-r">
      <div className="p-4 space-y-4">
        {emails.length === 0 && <div className="text-sm text-muted-foreground">No emails found.</div>}
        {emails.map(email => (
          <Card key={email.id} className="cursor-pointer hover:bg-accent transition-colors" onClick={() => onSelectEmail(email.id)}>
            <CardHeader className="p-4">
              <CardTitle className="text-sm font-medium">{email.subject || '(No Subject)'}</CardTitle>
              <CardDescription className="text-xs truncate">{email.sender}</CardDescription>
              <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{email.snippet}</p>
            </CardHeader>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/EmailList.tsx
git commit -m "feat: integrate actual backend data into EmailList"
```

### Task 3: Integrate Email Detail View

**Files:**
- Modify: `frontend/src/components/EmailDetail.tsx`

**Step 1: Write the minimal implementation**

Modify `frontend/src/components/EmailDetail.tsx` to fetch `/api/emails/{id}` and `/api/llm/summarize`:
```tsx
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
    setLoading(true);
    setEmail(null);
    setLlmData(null);

    const fetchData = async () => {
      try {
        const emailRes = await fetch(`http://localhost:8000/api/emails/${emailId}`);
        const emailJson = await emailRes.json();
        
        if (!isMounted) return;
        setEmail(emailJson);

        const llmRes = await fetch(`http://localhost:8000/api/llm/summarize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email_body: emailJson.body })
        });
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
```

**Step 2: Commit**

```bash
git add frontend/src/components/EmailDetail.tsx
git commit -m "feat: integrate EmailDetail with actual backend API and LLM summarization"
```
