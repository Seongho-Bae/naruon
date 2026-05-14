import { WorkspacePlaceholderPage } from '@/components/WorkspacePlaceholderPage';

export default async function LabelWorkspacePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <WorkspacePlaceholderPage eyebrow="Workspace / Label" title="라벨 워크스페이스 준비 중" description={`'${decodeURIComponent(slug)}' 라벨은 semantic 분류/owner scope가 구현되면 실제 필터 보드와 연결됩니다.`} />;
}
