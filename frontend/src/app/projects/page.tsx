import { WorkspacePlaceholderPage } from '@/components/WorkspacePlaceholderPage';

export default function ProjectsPage() {
  return (
    <WorkspacePlaceholderPage
      eyebrow="Projects"
      title="프로젝트 모음 준비 중"
      description="프로젝트별 메일, 실행 항목, 판단 포인트를 묶는 인덱스 화면입니다. 현재는 개별 프로젝트 워크스페이스로 연결되는 안전한 placeholder로 유지합니다."
      nextHref="/projects/launch"
      nextLabel="출시 프로젝트 보기"
    />
  );
}
