'use client';

import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { InsightCard } from '@/components/InsightCard';
import { CheckCircle2, Network, Target } from 'lucide-react';

const workspaceSections = [
  {
    href: '/ai-hub/context',
    title: '맥락 종합',
    description: '관련 메일, 관계, 일정 언급을 한 번에 묶어 지금 어떤 흐름이 열려 있는지 빠르게 훑습니다.',
    icon: <Network className="size-4" />,
    badge: 'CONTEXT',
  },
  {
    href: '/ai-hub/decisions',
    title: '판단 포인트',
    description: '무엇을 먼저 결정해야 하는지, 어떤 메일이 일정/조율/답장을 막고 있는지를 정리합니다.',
    icon: <Target className="size-4" />,
    badge: 'DECISIONS',
  },
  {
    href: '/ai-hub/actions',
    title: '실행 항목',
    description: '메일에서 바로 후속 작업과 일정 반영 후보를 추려 실행 보드로 넘깁니다.',
    icon: <CheckCircle2 className="size-4" />,
    badge: 'ACTIONS',
  },
];

export default function AIHubPage() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-6 lg:p-8">
      <header className="space-y-2">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-primary">Workspace overview</p>
        <h1 className="text-3xl font-black tracking-tight text-foreground">맥락 워크스페이스</h1>
        <p className="text-sm leading-6 text-muted-foreground">AI를 전면에 내세우기보다, 메일을 읽고 판단하고 실행하는 흐름을 세 개의 작업면으로 나눠 정리합니다.</p>
      </header>

      <div className="grid gap-4 lg:grid-cols-3">
        {workspaceSections.map((section) => (
          <Link key={section.href} href={section.href} className="rounded-3xl focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
            <InsightCard title={section.title} icon={section.icon} empty={false}>
              <div className="space-y-4">
                <Badge variant="secondary" className="border border-primary/10 bg-primary/10 text-primary">{section.badge}</Badge>
                <p>{section.description}</p>
                <p className="text-xs font-semibold text-primary">열기 →</p>
              </div>
            </InsightCard>
          </Link>
        ))}
      </div>
    </div>
  );
}
