import React from 'react';
import {
  CalendarDays,
  CheckCircle2,
  Inbox,
  Network,
  Search,
  Sparkles,
  Target,
} from 'lucide-react';

const navItems = [
  { label: '받은편지함', description: '우선순위 메일', icon: Inbox, active: true },
  { label: '맥락 종합', description: '흩어진 흐름 연결', icon: Network },
  { label: '판단 포인트', description: '의사결정 기준', icon: Target },
  { label: '실행 항목', description: '다음 행동 추적', icon: CheckCircle2 },
  { label: '일정 연결', description: '캘린더 반영', icon: CalendarDays },
];

function NaruonMark({
  className = 'h-8 w-8',
  idSuffix,
}: {
  className?: string;
  idSuffix: string;
}) {
  const flowId = `naruon-flow-${idSuffix}`;
  const sparkId = `naruon-spark-${idSuffix}`;

  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 64 64"
      className={className}
    >
      <defs>
        <linearGradient id={flowId} x1="10" y1="52" x2="48" y2="8" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C3AED" />
          <stop offset="0.45" stopColor="#2563FF" />
          <stop offset="1" stopColor="#38BDF8" />
        </linearGradient>
        <linearGradient id={sparkId} x1="40" y1="45" x2="58" y2="28" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22C55E" />
          <stop offset="1" stopColor="#86EFAC" />
        </linearGradient>
      </defs>
      <path
        d="M8 45C18 24 34 13 58 11C40 18 29 31 24 54C20 48 15 45 8 45Z"
        fill={`url(#${flowId})`}
      />
      <path
        d="M8 45C23 37 37 33 52 34C38 39 28 46 24 54C20 48 15 45 8 45Z"
        fill="#4F46E5"
        opacity="0.42"
      />
      <path
        d="M42 37C49 36 53 32 55 25C57 32 61 36 68 37C61 39 57 43 55 50C53 43 49 39 42 37Z"
        fill={`url(#${sparkId})`}
      />
      <path
        d="M20 11C24 10 26 8 27 4C28 8 30 10 34 11C30 12 28 14 27 18C26 14 24 12 20 11Z"
        fill="#2563FF"
      />
    </svg>
  );
}

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex h-screen overflow-hidden bg-background text-foreground">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-card focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary focus:shadow-lg focus:outline-none focus:ring-3 focus:ring-ring/40"
      >
        Skip to main content
      </a>
      <aside aria-label="Naruon workspace sidebar" className="hidden w-[17rem] shrink-0 flex-col border-r border-sidebar-border bg-sidebar/95 px-4 py-5 shadow-[8px_0_32px_rgba(15,23,42,0.04)] lg:flex">
        <div className="space-y-5">
          <div className="flex items-center gap-3">
            <NaruonMark idSuffix="sidebar" />
            <div>
              <p className="text-2xl font-black tracking-tight text-foreground">Naruon</p>
              <p className="text-xs font-medium text-muted-foreground">AI Email Workspace</p>
            </div>
          </div>
          <div className="rounded-2xl border border-primary/15 bg-primary/5 p-4 shadow-sm">
            <p className="text-sm font-bold text-foreground">흐름을 건너, 더 나은 판단과 실행으로.</p>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              이메일, 일정, 관계와 결정을 하나의 맥락으로 연결합니다.
            </p>
          </div>
        </div>

        <nav aria-label="Naruon workspace sections" className="mt-6 space-y-1.5">
          {navItems.map(({ label, description, icon: Icon, active }) => (
            <a
              key={label}
              href="#main-content"
              aria-current={active ? 'page' : undefined}
              className={`group flex min-h-12 items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
                active
                  ? 'bg-primary text-primary-foreground shadow-[0_10px_24px_rgba(37,99,255,0.22)]'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-primary'
              }`}
            >
              <Icon className="size-4" aria-hidden="true" />
              <span className="flex flex-col leading-tight">
                <span className="font-semibold">{label}</span>
                <span className={`text-[11px] ${active ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
                  {description}
                </span>
              </span>
            </a>
          ))}
        </nav>

        <div className="mt-auto rounded-2xl border border-border/80 bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Sparkles className="size-4 text-primary" aria-hidden="true" />
            Naruon AI 어시스턴트
          </div>
          <p className="mt-2 text-xs leading-5 text-muted-foreground">
            맥락 종합, 판단 포인트, 실행 항목을 한 화면에서 추적하세요.
          </p>
        </div>
      </aside>

      <main id="main-content" className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header aria-label="Naruon workspace header" className="flex min-h-16 items-center gap-4 border-b border-border/70 bg-card/80 px-4 backdrop-blur-xl lg:px-6">
          <div className="flex items-center gap-2 lg:hidden">
            <NaruonMark className="h-7 w-7" idSuffix="header" />
            <span className="text-lg font-black tracking-tight">Naruon</span>
          </div>
          <div className="hidden min-w-0 flex-1 items-center rounded-2xl border border-border bg-background/80 px-4 py-2 text-sm text-muted-foreground shadow-inner shadow-slate-950/[0.02] md:flex">
            <Search className="mr-2 size-4 text-primary" aria-hidden="true" />
            Search context, people, files, and insights
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              맥락 종합
            </span>
            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700">
              실행 중심
            </span>
          </div>
        </header>
        <section className="min-h-0 flex-1 overflow-hidden p-3 lg:p-4">
          {children}
        </section>
      </main>
    </div>
  );
}
