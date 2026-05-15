import { describe, expect, it } from 'vitest';

import { deriveWorkspaceInsights, summarizeTodayInsight } from './workspace-insights';

describe('workspace insights', () => {
  it('derives judgment, coordination, and action counts from inbox emails', () => {
    const insights = deriveWorkspaceInsights([
      {
        id: 1,
        subject: '출시 일정 검토 요청',
        snippet: '우선순위를 조정해야 합니다.',
        unread: true,
        reply_count: 3,
      },
      {
        id: 2,
        subject: '회의 일정 확인',
        snippet: '일정과 참석자를 확인해 주세요.',
        unread: false,
        reply_count: 1,
      },
      {
        id: 3,
        subject: '주간 리포트',
        snippet: '공유드립니다.',
        unread: true,
        reply_count: 1,
      },
    ]);

    expect(insights.judgmentCount).toBe(2);
    expect(insights.coordinationCount).toBe(1);
    expect(insights.actionCount).toBe(2);
  });

  it('builds today insight copy from email-derived workload signals', () => {
    const summary = summarizeTodayInsight({
      judgmentCount: 4,
      coordinationCount: 2,
      actionCount: 5,
    });

    expect(summary.title).toContain('오늘의 인사이트');
    expect(summary.highlights).toEqual([
      '우선 검토 4건',
      '조율 필요 2건',
      '실행 대기 5건',
    ]);
    expect(summary.description).toContain('이메일에서 바로 확인된 흐름');
  });
});
