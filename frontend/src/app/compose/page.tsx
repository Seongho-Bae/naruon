import { ComposePageClient } from './ComposePageClient';

export default async function ComposePage({ searchParams }: { searchParams?: Promise<{ emailId?: string }> }) {
  const params = searchParams ? await searchParams : undefined;
  return <ComposePageClient emailId={params?.emailId} />;
}
