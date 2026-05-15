export interface WorkspaceInsightEmail {
  id: number;
  subject: string | null;
  snippet: string;
  unread?: boolean;
  reply_count?: number;
}

export interface WorkspaceInsightCounts {
  judgmentCount: number;
  coordinationCount: number;
  actionCount: number;
}

const ACTION_KEYWORDS = ['검토', '요청', '일정', '회의', '확인', '조정', '답장', '후속'];

function containsActionKeyword(value: string) {
  return ACTION_KEYWORDS.some((keyword) => value.includes(keyword));
}

export function deriveWorkspaceInsights(emails: WorkspaceInsightEmail[]): WorkspaceInsightCounts {
  const judgmentCount = emails.filter((email) => email.unread).length;
  const coordinationCount = emails.filter((email) => (email.reply_count || 0) > 1).length;
  const actionCount = emails.filter((email) => {
    const haystack = `${email.subject || ''} ${email.snippet}`;
    return containsActionKeyword(haystack);
  }).length;

  return {
    judgmentCount,
    coordinationCount,
    actionCount,
  };
}

export function summarizeTodayInsight(counts: WorkspaceInsightCounts) {
  return {
    title: '오늘의 인사이트',
    description: '이메일에서 바로 확인된 흐름 기준으로 오늘 먼저 볼 일과 조율, 실행 대기를 압축했습니다.',
    highlights: [
      `우선 검토 ${counts.judgmentCount}건`,
      `조율 필요 ${counts.coordinationCount}건`,
      `실행 대기 ${counts.actionCount}건`,
    ],
  };
}
