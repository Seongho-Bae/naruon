import { WorkspaceHome } from '@/components/WorkspaceHome';
import type { MailFolder } from '@/components/EmailList';

type MailPageProps = {
  searchParams?: Promise<{
    folder?: string | string[];
  }>;
};

function normalizeMailFolder(value: string | string[] | undefined): MailFolder {
  const rawValue = Array.isArray(value) ? value[0] : value;
  return rawValue === 'sent' ? 'sent' : 'inbox';
}

export default async function MailPage({ searchParams }: MailPageProps) {
  const params = searchParams ? await searchParams : {};
  return <WorkspaceHome forcedStartupView="email" mailFolder={normalizeMailFolder(params.folder)} />;
}
