import { WorkspacePlaceholderPage } from '@/components/WorkspacePlaceholderPage';

const workspaceNames: Record<string, string> = {
  launch: '런칭 프로젝트',
  vendor: '벤더 관리',
  marketing: '마케팅 캠페인',
};

function resolveWorkspaceName(workspace?: string) {
  if (!workspace) {
    return null;
  }
  return workspaceNames[workspace] ?? decodeURIComponent(workspace);
}

export default async function ProjectsPage({ searchParams }: { searchParams?: Promise<{ workspace?: string }> } = {}) {
  const params = searchParams ? await searchParams : {};
  const selectedWorkspace = resolveWorkspaceName(params.workspace);

  return (
    <WorkspacePlaceholderPage
      eyebrow="Projects"
      title={selectedWorkspace ? `${selectedWorkspace} 워크스페이스 준비 중` : '프로젝트 모음 준비 중'}
      description={
        selectedWorkspace
          ? `${selectedWorkspace} 프로젝트는 ExecutionItem ↔ WBS 연결 이후 실제 프로젝트 보드와 연결됩니다.`
          : '프로젝트별 메일, 실행 항목, 판단 포인트를 묶는 인덱스 화면입니다. 현재는 쿼리 기반 placeholder로 안전하게 유지합니다.'
      }
      nextHref={selectedWorkspace ? '/projects' : '/projects?workspace=launch'}
      nextLabel={selectedWorkspace ? '프로젝트 목록 보기' : '런칭 프로젝트 보기'}
    />
  );
}
