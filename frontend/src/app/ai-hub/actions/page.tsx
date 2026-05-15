'use client';

import { useEffect, useMemo, useState } from 'react';

import { apiClient } from '@/lib/api-client';
import { listExecutionQueue, refreshExecutionQueue, subscribeExecutionQueue, type ExecutionQueueItem } from '@/lib/execution-queue';
import { type WorkspaceInsightEmail } from '@/lib/workspace-insights';
import { InsightCard } from '@/components/InsightCard';
import { CheckCircle2, CalendarDays, Repeat } from 'lucide-react';

interface MailboxAccountSummary {
  id: number;
  email_address: string;
  display_name: string | null;
  is_default_reply: boolean;
  is_active: boolean;
}

function buildExecutionBacklog(emails: WorkspaceInsightEmail[]) {
  return emails
    .filter((email) => `${email.subject || ''} ${email.snippet}`.match(/검토|요청|회의|일정|확인|조정/))
    .slice(0, 6)
    .map((email) => ({
      id: email.id,
      title: email.subject || '(제목 없음)',
      note: email.snippet,
      followUp: (email.reply_count || 0) > 1 ? '조율 후 답장' : '답장 또는 일정 확인',
    }));
}

export default function AIHubActionsPage() {
  const [emails, setEmails] = useState<WorkspaceInsightEmail[]>([]);
  const [queueItems, setQueueItems] = useState<ExecutionQueueItem[]>([]);
  const [mailboxAccounts, setMailboxAccounts] = useState<MailboxAccountSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const syncQueue = () => setQueueItems(listExecutionQueue());
    syncQueue();
    void refreshExecutionQueue().then(setQueueItems);
    return subscribeExecutionQueue(syncQueue);
  }, []);

  useEffect(() => {
    let active = true;
    const loadMailboxAccounts = async () => {
      try {
        const data = await apiClient.get<{ items: MailboxAccountSummary[] }>('/api/mailbox-accounts');
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

  useEffect(() => {
    let active = true;
    const loadEmails = async () => {
      try {
        const data = await apiClient.get<{ emails: WorkspaceInsightEmail[] }>('/api/emails?limit=24');
        if (!active) return;
        setEmails(data.emails || []);
      } catch (err: unknown) {
        if (!active) return;
        setError((err as Error).message || '실행 항목을 불러오지 못했습니다.');
      } finally {
        if (active) setLoading(false);
      }
    };
    void loadEmails();
    return () => {
      active = false;
    };
  }, []);

  const backlog = useMemo(() => {
    const queuedIds = new Set(queueItems.filter((item) => item.status === 'queued').map((item) => item.sourceEmailId).filter((value): value is number => value !== null));
    return buildExecutionBacklog(emails).filter((item) => !queuedIds.has(item.id));
  }, [emails, queueItems]);
  const queuedItems = useMemo(() => queueItems.filter((item) => item.status === 'queued'), [queueItems]);
  const mailboxLabel = (mailboxAccountId?: number | null) => {
    if (!mailboxAccountId) return null;
    const account = mailboxAccounts.find((item) => item.id === mailboxAccountId);
    return account ? (account.display_name || account.email_address) : null;
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-6 lg:p-8">
      <header className="space-y-2">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-emerald-700">Workspace / Actions</p>
        <h1 className="text-3xl font-black tracking-tight text-foreground">실행 항목</h1>
        <p className="text-sm leading-6 text-muted-foreground">메일에서 바로 이어지는 답장, 일정, 후속 조치를 실행 보드로 넘깁니다.</p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <InsightCard title="실행 백로그" icon={<CheckCircle2 className="size-4" />} loading={loading} error={error} empty={!loading && queuedItems.length + backlog.length === 0} emptyMessage="실행으로 넘길 메일이 없습니다.">
          <ul className="space-y-3">
            {queuedItems.map((item) => (
              <li key={`queue-${item.id}`} className="rounded-xl border border-primary/15 bg-primary/5 px-4 py-3 text-sm">
                <div className="flex items-start justify-between gap-3">
                  <p className="font-semibold text-foreground">{item.title}</p>
                  {mailboxLabel(item.sourceMailboxAccountId) ? (
                    <span className="rounded-full border border-primary/20 bg-background/80 px-2 py-1 text-[10px] font-bold text-primary">
                      {mailboxLabel(item.sourceMailboxAccountId)}
                    </span>
                  ) : null}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{item.sender}</p>
                {item.sourceSnippet ? <p className="mt-1 text-xs text-muted-foreground">{item.sourceSnippet}</p> : null}
                <p className="mt-2 text-xs font-semibold text-primary">스와이프로 담긴 실행 항목</p>
              </li>
            ))}
            {backlog.map((item) => (
              <li key={item.id} className="rounded-xl border border-emerald-500/15 bg-emerald-500/5 px-4 py-3 text-sm">
                <p className="font-semibold text-foreground">{item.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">{item.note}</p>
                <p className="mt-2 text-xs font-semibold text-emerald-700">다음 행동: {item.followUp}</p>
              </li>
            ))}
          </ul>
        </InsightCard>

        <div className="grid gap-4">
          <div id="calendar-bridge">
          <InsightCard title="캘린더 연결" icon={<CalendarDays className="size-4" />} loading={loading} error={error} empty={false}>
            <p>일정 언급 메일은 답장 전에 캘린더 후보로 보냅니다. 모바일에서는 메일 스와이프로 바로 실행 보드에 담을 수 있게 연결합니다.</p>
          </InsightCard>
          </div>
          <InsightCard title="반복 처리 흐름" icon={<Repeat className="size-4" />} loading={loading} error={error} empty={false}>
            <p>검토 → 판단 → 실행의 순서를 유지해 메일 읽기와 후속 작업 관리가 분리되지 않도록 구성합니다.</p>
          </InsightCard>
        </div>
      </div>
    </div>
  );
}
