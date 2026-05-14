'use client';

import { useEffect, useMemo, useState } from 'react';

import { apiClient } from '@/lib/api-client';
import { deriveWorkspaceInsights, type WorkspaceInsightEmail } from '@/lib/workspace-insights';
import { InsightCard } from '@/components/InsightCard';
import { Target, AlertTriangle } from 'lucide-react';

function buildDecisionAgenda(emails: WorkspaceInsightEmail[], judgmentCount: number, coordinationCount: number) {
  const items = [
    `우선 검토 ${judgmentCount}건 중 오늘 답을 내야 하는 메일을 먼저 고릅니다.`,
    `조율 필요 ${coordinationCount}건은 담당자/일정/답장 순서를 명확히 해야 합니다.`,
  ];

  const scheduled = emails.find((email) => `${email.subject || ''} ${email.snippet}`.includes('일정'));
  if (scheduled) {
    items.push(`일정 언급 메일 '${scheduled.subject || '(제목 없음)'}'의 캘린더 반영 여부를 결정합니다.`);
  }

  return items;
}

export default function AIHubDecisionsPage() {
  const [emails, setEmails] = useState<WorkspaceInsightEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadEmails = async () => {
      try {
        const data = await apiClient.get<{ emails: WorkspaceInsightEmail[] }>('/api/emails?limit=24');
        if (!active) return;
        setEmails(data.emails || []);
      } catch (err: unknown) {
        if (!active) return;
        setError((err as Error).message || '판단 포인트를 불러오지 못했습니다.');
      } finally {
        if (active) setLoading(false);
      }
    };
    void loadEmails();
    return () => {
      active = false;
    };
  }, []);

  const insights = useMemo(() => deriveWorkspaceInsights(emails), [emails]);
  const agenda = useMemo(() => buildDecisionAgenda(emails, insights.judgmentCount, insights.coordinationCount), [emails, insights]);

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-6 lg:p-8">
      <header className="space-y-2">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-violet-700">Workspace / Decisions</p>
        <h1 className="text-3xl font-black tracking-tight text-foreground">판단 포인트</h1>
        <p className="text-sm leading-6 text-muted-foreground">답장, 일정, 후속 실행으로 넘어가기 전에 먼저 결정해야 하는 쟁점을 추립니다.</p>
      </header>

      <InsightCard title="오늘 결정할 것" icon={<Target className="size-4" />} loading={loading} error={error} empty={!loading && agenda.length === 0}>
        <ul className="space-y-3">
          {agenda.map((item) => (
            <li key={item} className="rounded-xl border border-violet-500/15 bg-violet-500/5 px-4 py-3 text-sm leading-6">{item}</li>
          ))}
        </ul>
      </InsightCard>

      <InsightCard title="리스크 메모" icon={<AlertTriangle className="size-4" />} loading={loading} error={error} empty={!loading && emails.length === 0}>
        <p>다자간 조율 메일은 담당 주체와 마감이 흐려지기 쉽습니다. 메일 스레드를 실행 항목으로 밀어 넣기 전에 담당자와 일정, 필요한 답장 순서를 확정하세요.</p>
      </InsightCard>
    </div>
  );
}
