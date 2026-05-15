import { WorkspacePlaceholderPage } from '@/components/WorkspacePlaceholderPage';

const labelNames: Record<string, string> = {
  urgent: '긴급',
  meeting: '회의',
  contract: '계약',
  design: '디자인',
  dev: '개발',
};

function resolveLabelName(label?: string) {
  if (!label) {
    return null;
  }
  return labelNames[label] ?? decodeURIComponent(label);
}

export default async function LabelsPage({ searchParams }: { searchParams?: Promise<{ label?: string }> } = {}) {
  const params = searchParams ? await searchParams : {};
  const selectedLabel = resolveLabelName(params.label);

  return (
    <WorkspacePlaceholderPage
      eyebrow="Labels"
      title={selectedLabel ? `${selectedLabel} 라벨 워크스페이스 준비 중` : '라벨 모음 준비 중'}
      description={
        selectedLabel
          ? `${selectedLabel} 라벨은 semantic 분류/owner scope가 구현되면 실제 필터 보드와 연결됩니다.`
          : '라벨별 메일 필터와 실행 항목을 탐색하는 인덱스 화면입니다. 현재는 쿼리 기반 placeholder로 안전하게 유지합니다.'
      }
      nextHref={selectedLabel ? '/labels' : '/labels?label=urgent'}
      nextLabel={selectedLabel ? '라벨 목록 보기' : '긴급 라벨 보기'}
    />
  );
}
