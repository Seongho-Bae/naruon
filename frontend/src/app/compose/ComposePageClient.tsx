'use client';

import { useEffect, useMemo, useState } from 'react';

import { apiClient } from '@/lib/api-client';
import { buildReplyPayload, type ThreadEmailData } from '@/lib/email-threading';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Mail, PenLine, SendHorizonal } from 'lucide-react';

interface MailboxAccountOption {
  id: number;
  email_address: string;
  display_name: string | null;
  is_default_reply: boolean;
  is_active: boolean;
}

export function ComposePageClient({ emailId }: { emailId?: string }) {
  const [mailboxAccounts, setMailboxAccounts] = useState<MailboxAccountOption[]>([]);
  const [selectedMailboxAccountId, setSelectedMailboxAccountId] = useState<number | null>(null);
  const [sourceEmail, setSourceEmail] = useState<ThreadEmailData | null>(null);
  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [instruction, setInstruction] = useState('정중하게 답장 초안을 작성해줘');
  const [loading, setLoading] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadMailboxAccounts = async () => {
      try {
        const data = await apiClient.get<{ items: MailboxAccountOption[] }>('/api/mailbox-accounts');
        if (!active) return;
        setMailboxAccounts(data.items || []);
        const defaultAccount = data.items.find((item) => item.is_default_reply && item.is_active) || data.items[0] || null;
        setSelectedMailboxAccountId(defaultAccount?.id ?? null);
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

  useEffect(() => {
    if (!emailId) return;
    let active = true;
    const loadSourceEmail = async () => {
      setLoading(true);
      setError(null);
      try {
        const email = await apiClient.get<ThreadEmailData>(`/api/emails/${emailId}`);
        if (!active) return;
        setSourceEmail(email);
        setTo(email.reply_to || email.sender || '');
        setSubject(email.subject ? `Re: ${email.subject}` : 'Re: (제목 없음)');
        if (email.mailbox_account_id) {
          setSelectedMailboxAccountId(email.mailbox_account_id);
        }
      } catch (err: unknown) {
        if (!active) return;
        setError((err as Error).message || '답장 대상 메일을 불러오지 못했습니다.');
      } finally {
        if (active) setLoading(false);
      }
    };
    void loadSourceEmail();
    return () => {
      active = false;
    };
  }, [emailId]);

  const hint = useMemo(() => {
    if (sourceEmail) {
      return `${sourceEmail.subject || '(제목 없음)'} 메일을 기준으로 답장 흐름을 이어갑니다.`;
    }
    return '새 메일을 작성하거나, 받은편지함에서 선택한 메일의 답장 초안을 이어서 작성할 수 있습니다.';
  }, [sourceEmail]);

  const handleDraft = async () => {
    if (!sourceEmail) {
      setStatus('선택된 원본 메일이 없어서 일반 메일 작성 모드로 유지합니다.');
      return;
    }
    setDrafting(true);
    setError(null);
    setStatus(null);
    try {
      const draft = await apiClient.post<{ draft: string }>('/api/llm/draft', {
        email_body: sourceEmail.body,
        instruction,
      });
      setBody(draft.draft || '');
    } catch (err: unknown) {
      setError((err as Error).message || '답장 초안을 만들지 못했습니다.');
    } finally {
      setDrafting(false);
    }
  };

  const handleSend = async () => {
    if (!to || !subject || !body) {
      setError('받는 사람, 제목, 본문을 모두 입력하세요.');
      return;
    }
    setSending(true);
    setError(null);
    setStatus(null);
    try {
      const payload = {
        ...(sourceEmail
          ? buildReplyPayload(sourceEmail, body, { to, subject })
          : { to, subject, body }),
        ...(selectedMailboxAccountId ? { mailbox_account_id: selectedMailboxAccountId } : {}),
      };
      const result = await apiClient.post<{ simulated?: boolean }>('/api/emails/send', payload);
      setStatus(result.simulated ? '개발 모드에서 메일 전송을 시뮬레이션했습니다.' : '메일을 전송했습니다.');
      if (!sourceEmail) {
        setBody('');
      }
    } catch (err: unknown) {
      setError((err as Error).message || '메일 전송에 실패했습니다.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 p-6 lg:p-8">
      <header className="space-y-2">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-primary">Mail / Compose</p>
        <h1 className="flex items-center gap-2 text-3xl font-black tracking-tight text-foreground"><Mail className="size-6 text-primary" />메일 작성</h1>
        <p className="text-sm leading-6 text-muted-foreground">{hint}</p>
      </header>

      <section className="rounded-3xl border border-border bg-card p-6 shadow-sm space-y-4">
        {loading ? <p className="text-sm text-muted-foreground">원본 메일을 불러오는 중입니다...</p> : null}
        {error ? <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
        {status ? <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3 text-sm text-emerald-700">{status}</div> : null}

        <div className="grid gap-4">
          {mailboxAccounts.length > 0 ? (
            <div className="space-y-2">
              <label className="text-sm font-semibold">회신 계정</label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={selectedMailboxAccountId ?? ''}
                onChange={(event) => setSelectedMailboxAccountId(event.target.value ? Number(event.target.value) : null)}
              >
                {mailboxAccounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {(account.display_name || account.email_address) + (account.is_default_reply ? ' · 기본 회신' : '')}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
          <Input aria-label="받는 사람" placeholder="받는 사람" value={to} onChange={(event) => setTo(event.target.value)} />
          <Input aria-label="메일 제목" placeholder="메일 제목" value={subject} onChange={(event) => setSubject(event.target.value)} />
          <Textarea aria-label="메일 본문" className="min-h-[240px]" placeholder="보낼 내용을 작성하세요." value={body} onChange={(event) => setBody(event.target.value)} />
        </div>

        <div className="grid gap-3 rounded-2xl border border-border bg-background/70 p-4">
          <Input aria-label="답장 초안 지시" placeholder="예: 일정 확인을 포함해 정중하게 작성" value={instruction} onChange={(event) => setInstruction(event.target.value)} />
          <div className="flex flex-wrap gap-3">
            <Button type="button" variant="outline" onClick={handleDraft} disabled={drafting || !sourceEmail}><PenLine className="mr-2 size-4" />{drafting ? '초안 생성 중...' : '답장 초안'}</Button>
            <Button type="button" onClick={handleSend} disabled={sending}><SendHorizonal className="mr-2 size-4" />{sending ? '전송 중...' : '메일 보내기'}</Button>
          </div>
        </div>
      </section>
    </div>
  );
}
