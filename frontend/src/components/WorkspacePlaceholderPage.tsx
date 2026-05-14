import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export function WorkspacePlaceholderPage({
  eyebrow,
  title,
  description,
  nextHref = '/',
  nextLabel = '받은편지함으로 돌아가기',
}: {
  eyebrow: string;
  title: string;
  description: string;
  nextHref?: string;
  nextLabel?: string;
}) {
  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 p-6 lg:p-8">
      <header className="space-y-2">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-primary">{eyebrow}</p>
        <h1 className="text-3xl font-black tracking-tight text-foreground">{title}</h1>
        <p className="text-sm leading-6 text-muted-foreground">{description}</p>
      </header>

      <section className="rounded-3xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="secondary" className="border border-primary/10 bg-primary/10 text-primary">WORK IN PROGRESS</Badge>
          <span className="text-sm text-muted-foreground">mailbox ownership와 folder/project/label semantic 모델이 완료되면 실제 데이터와 연결됩니다.</span>
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href={nextHref} className={cn(buttonVariants({ variant: 'default' }))}>{nextLabel}</Link>
          <Link href="/ai-hub/actions" className={cn(buttonVariants({ variant: 'outline' }))}>실행 항목 보기</Link>
        </div>
      </section>
    </div>
  );
}
