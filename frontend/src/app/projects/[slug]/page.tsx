import { WorkspacePlaceholderPage } from '@/components/WorkspacePlaceholderPage';

export default async function ProjectWorkspacePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <WorkspacePlaceholderPage eyebrow="Workspace / Project" title="프로젝트 워크스페이스 준비 중" description={`'${decodeURIComponent(slug)}' 프로젝트는 ExecutionItem ↔ WBS 연결 이후 실제 프로젝트 보드와 연결됩니다.`} />;
}
