'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { InsightCard } from '@/components/InsightCard';
import { Network, Sparkles, BookOpen } from 'lucide-react';

export default function AIHubPage() {
  const [prompts, setPrompts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await apiClient.get<any[]>('/api/prompts');
        setPrompts(data);
      } catch (err: unknown) {
        setError(((err as Error).message || '') || "데이터를 불러오는 데 실패했습니다.");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-black text-foreground flex items-center gap-2 mb-2">
          <Network className="w-6 h-6 text-primary" />
          AI Hub
        </h1>
        <p className="text-muted-foreground text-sm">최근 인사이트와 저장된 프롬프트를 확인하세요.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <InsightCard 
          title="최근 AI 요약" 
          icon={<Sparkles className="w-4 h-4" />}
          loading={loading}
          error={error}
          empty={!loading && prompts.length === 0}
          emptyMessage="저장된 프롬프트나 최근 요약이 없습니다."
        >
          <div className="space-y-4">
            {prompts.map(p => (
              <div key={p.id} className="p-3 bg-secondary/20 rounded-lg border border-border">
                <h4 className="font-bold text-sm flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-primary" />
                  {p.title}
                </h4>
                <p className="text-xs text-muted-foreground mt-1 truncate">{p.description || "설명 없음"}</p>
              </div>
            ))}
          </div>
        </InsightCard>
      </div>
    </div>
  );
}
