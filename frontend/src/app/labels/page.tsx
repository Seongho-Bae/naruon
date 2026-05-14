import { WorkspacePlaceholderPage } from '@/components/WorkspacePlaceholderPage';

export default function LabelsPage() {
  return (
    <WorkspacePlaceholderPage
      eyebrow="Labels"
      title="라벨 모음 준비 중"
      description="라벨별 메일 필터와 실행 항목을 탐색하는 인덱스 화면입니다. 현재는 개별 라벨 워크스페이스로 연결되는 안전한 placeholder로 유지합니다."
      nextHref="/labels/urgent"
      nextLabel="긴급 라벨 보기"
    />
  );
}
