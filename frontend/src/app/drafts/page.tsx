import { WorkspacePlaceholderPage } from '@/components/WorkspacePlaceholderPage';

export default function DraftsPage() {
  return <WorkspacePlaceholderPage eyebrow="Mailbox / Drafts" title="임시 보관함 보드 준비 중" description="답장 초안과 발송 전 검토 흐름은 compose/session 모델이 완성되면 이 화면과 연결됩니다." nextHref="/compose" nextLabel="메일 작성 열기" />;
}
