'use client';

import { useEffect, useMemo, useState } from 'react';

import { apiClient } from '@/lib/api-client';
import { deriveWorkspaceInsights, type WorkspaceInsightEmail } from '@/lib/workspace-insights';
import { InsightCard } from '@/components/InsightCard';
import { Network, Users, FileText } from 'lucide-react';

export default function AIHubContextPage() {
  const [emails, setEmails] = useState<WorkspaceInsightEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const searchQuery = typeof window === 'undefined'
    ? ''
    : (new URLSearchParams(window.location.search).get('q') || '').trim();

  useEffect(() => {
    let active = true;
    const loadEmails = async () => {
      try {
        const data = searchQuery
          ? await apiClient.post<{ results: WorkspaceInsightEmail[] }>('/api/search', { query: searchQuery })
          : await apiClient.get<{ emails: WorkspaceInsightEmail[] }>('/api/emails?limit=24');
        if (!active) return;
        setEmails('results' in data ? data.results || [] : data.emails || []);
      } catch (err: unknown) {
        if (!active) return;
        setError((err as Error).message || '맥락 데이터를 불러오지 못했습니다.');
      } finally {
        if (active) setLoading(false);
      }
    };
    void loadEmails();
    return () => {
      active = false;
    };
  }, [searchQuery]);

  const insights = useMemo(() => deriveWorkspaceInsights(emails), [emails]);

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-6 lg:p-8">
      <header className="space-y-2">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-primary">Workspace / Context</p>
        <h1 className="text-3xl font-black tracking-tight text-foreground">맥락 종합</h1>
        <p className="text-sm leading-6 text-muted-foreground">최근 메일에서 지금 검토, 조율, 실행으로 이어질 흐름을 한 번에 훑습니다.</p>
        {searchQuery ? <p className="text-sm font-semibold text-primary">검색어: {searchQuery}</p> : null}
      </header>

      <div className="grid gap-4 lg:grid-cols-3">
        <InsightCard title="검토 중인 흐름" icon={<Network className="size-4" />} loading={loading} error={error} empty={!loading && emails.length === 0}>
          <p>우선 검토 메일 {insights.judgmentCount}건이 현재 맥락의 시작점입니다.</p>
        </InsightCard>
        <InsightCard title="관계/조율" icon={<Users className="size-4" />} loading={loading} error={error} empty={!loading && emails.length === 0}>
          <p>여러 번 왕복된 대화 {insights.coordinationCount}건을 우선 조율 대상으로 봅니다.</p>
        </InsightCard>
        <InsightCard title="근거가 되는 메일" icon={<FileText className="size-4" />} loading={loading} error={error} empty={!loading && emails.length === 0}>
          <ul className="space-y-2">
            {emails.slice(0, 4).map((email) => (
              <li key={email.id} className="rounded-xl border border-border/70 bg-background/70 px-3 py-2 text-sm">
                <p className="font-semibold text-foreground">{email.subject || '(제목 없음)'}</p>
                <p className="mt-1 text-xs text-muted-foreground">{email.snippet}</p>
              </li>
            ))}
          </ul>
        </InsightCard>
      </div>
    </div>
  );
}
