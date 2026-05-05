import React from 'react';
import {
  AppWindow,
  Archive,
  Bell,
  CalendarDays,
  CircleHelp,
  Database,
  Folder,
  Home,
  Inbox,
  LayoutDashboard,
  Mail,
  Paperclip,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Star,
  Users,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const globalNavItems = [
  { label: '홈', icon: Home },
  { label: '대시보드', icon: LayoutDashboard },
  { label: '메일', icon: Mail, active: true },
  { label: '일정', icon: CalendarDays },
  { label: '프로젝트', icon: Folder },
  { label: '데이터', icon: Database },
  { label: 'AI 허브', icon: Sparkles },
  { label: '보안', icon: ShieldCheck },
  { label: '설정', icon: Settings },
];

const mailboxItems = [
  { label: '받은편지함', count: 248, icon: Inbox, active: true },
  { label: '중요', count: 18, icon: Star },
  { label: 'AI 종합', count: 12, icon: Sparkles, badge: 'NEW' },
  { label: '첨부', count: 132, icon: Paperclip },
  { label: '보관함', count: 36, icon: Archive },
];

const folderItems = [
  { label: '고객사', count: 96 },
  { label: '프로젝트', count: 74 },
  { label: '파트너사', count: 22 },
  { label: '마케팅', count: 8 },
];

function NaruonMark({ className = 'size-9', idSuffix }: { className?: string; idSuffix: string }) {
  const flowId = `naruon-flow-${idSuffix}`;
  const sparkId = `naruon-spark-${idSuffix}`;

  return (
    <svg aria-hidden="true" viewBox="0 0 64 64" className={className}>
      <defs>
        <linearGradient id={flowId} x1="8" y1="56" x2="54" y2="8" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C3AED" />
          <stop offset="0.5" stopColor="#2563EB" />
          <stop offset="1" stopColor="#38BDF8" />
        </linearGradient>
        <linearGradient id={sparkId} x1="40" y1="46" x2="58" y2="27" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22C55E" />
          <stop offset="1" stopColor="#86EFAC" />
        </linearGradient>
      </defs>
      <path d="M7 45C18 24 35 12 59 10C42 18 30 31 24 55C20 49 15 45 7 45Z" fill={`url(#${flowId})`} />
      <path d="M7 45C23 37 38 33 53 34C39 39 29 46 24 55C20 49 15 45 7 45Z" fill="#4F46E5" opacity="0.42" />
      <path d="M41 37C49 36 53 32 55 25C57 32 61 36 69 37C61 39 57 43 55 51C53 43 49 39 41 37Z" fill={`url(#${sparkId})`} />
      <path d="M20 11C24 10 26 8 27 4C28 8 30 10 34 11C30 12 28 14 27 18C26 14 24 12 20 11Z" fill="#2563EB" />
    </svg>
  );
}

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
      <a
        href="#workspace-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-card focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary focus:shadow-lg focus:outline-none focus:ring-3 focus:ring-ring/40"
      >
        본문으로 건너뛰기
      </a>

      <header className="flex h-16 shrink-0 items-center gap-4 border-b border-border/80 bg-card/95 px-4 shadow-[0_1px_20px_rgba(15,23,42,0.04)] backdrop-blur-xl lg:px-6">
        <div className="flex min-w-[180px] items-center gap-3">
          <NaruonMark idSuffix="gnb" />
          <div className="leading-tight">
            <p className="text-xl font-black tracking-tight text-[#0B132B]">Naruon</p>
            <p className="text-[11px] font-medium text-muted-foreground">AI Email Workspace</p>
          </div>
        </div>

        <nav aria-label="전역 메뉴" className="hidden min-w-0 items-center gap-1 xl:flex">
          {globalNavItems.map(({ label, icon: Icon, active }) => (
            <a
              key={label}
              href={`#${label}`}
              aria-current={active ? 'page' : undefined}
              className={`group flex h-10 items-center gap-1.5 rounded-xl px-3 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
                active
                  ? 'bg-primary/10 text-primary shadow-inner shadow-primary/5'
                  : 'text-slate-600 hover:bg-muted hover:text-foreground'
              }`}
            >
              <Icon className="size-4" aria-hidden="true" />
              {label}
            </a>
          ))}
        </nav>

        <div className="relative ml-auto hidden min-w-[260px] max-w-md flex-1 md:block xl:max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-primary" aria-hidden="true" />
          <Input className="h-10 rounded-xl bg-muted/45 pl-9 shadow-inner shadow-slate-950/[0.02]" placeholder="검색 (⌘K)" aria-label="전체 검색" />
        </div>

        <div className="ml-auto flex items-center gap-1 md:ml-0">
          <Button variant="ghost" size="icon-lg" aria-label="알림">
            <Bell className="size-4" aria-hidden="true" />
          </Button>
          <Button variant="ghost" size="icon-lg" aria-label="도움말">
            <CircleHelp className="size-4" aria-hidden="true" />
          </Button>
          <Button variant="ghost" size="icon-lg" aria-label="앱 런처">
            <AppWindow className="size-4" aria-hidden="true" />
          </Button>
          <div className="hidden items-center gap-3 rounded-full border bg-background px-2 py-1 pl-1.5 sm:flex">
            <div className="grid size-8 place-items-center rounded-full bg-gradient-to-br from-primary to-[#7C3AED] text-xs font-bold text-white">김</div>
            <div className="pr-2 leading-tight">
              <p className="text-xs font-bold">김나루</p>
              <p className="text-[10px] text-muted-foreground">Naruon PM</p>
            </div>
          </div>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <aside aria-label="메일 폴더" className="hidden w-[236px] shrink-0 flex-col border-r border-border/80 bg-card/75 px-4 py-4 lg:flex">
          <Button className="mb-4 h-11 rounded-xl text-sm shadow-[0_12px_24px_rgba(37,99,235,0.18)]" type="button">
            <Mail className="mr-1 size-4" aria-hidden="true" />새 메일
          </Button>

          <nav aria-label="메일 폴더" className="space-y-1">
            <div className="space-y-1">
              <p className="px-2 pb-2 text-xs font-bold text-[#0B132B]">메일</p>
              {mailboxItems.map(({ label, count, icon: Icon, active, badge }) => (
                <a
                  key={label}
                  href={`#${label}`}
                  aria-current={active ? 'page' : undefined}
                  className={`flex min-h-10 items-center gap-2 rounded-xl px-2.5 text-sm transition focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
                    active ? 'bg-primary/10 font-bold text-primary' : 'text-slate-600 hover:bg-muted hover:text-foreground'
                  }`}
                >
                  <Icon className="size-4" aria-hidden="true" />
                  <span className="min-w-0 flex-1 truncate">{label}</span>
                  {badge ? <span className="rounded-full bg-[#7C3AED]/10 px-1.5 text-[10px] font-bold text-[#7C3AED]">{badge}</span> : null}
                  <span className="text-xs text-muted-foreground">{count}</span>
                </a>
              ))}
            </div>

            <div className="mt-6 space-y-1 border-t pt-4">
              <div className="flex items-center justify-between px-2 pb-2">
                <p className="text-xs font-bold text-[#0B132B]">내 폴더</p>
                <Users className="size-3.5 text-muted-foreground" aria-hidden="true" />
              </div>
              {folderItems.map(({ label, count }) => (
                <a key={label} href={`#${label}`} className="flex min-h-9 items-center gap-2 rounded-lg px-2.5 text-sm text-slate-600 transition hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
                  <Folder className="size-4" aria-hidden="true" />
                  <span className="flex-1">{label}</span>
                  <span className="text-xs text-muted-foreground">{count}</span>
                </a>
              ))}
            </div>
          </nav>

          <div className="mt-auto rounded-2xl border bg-gradient-to-br from-primary/8 via-card to-[#22C55E]/8 p-4">
            <p className="text-sm font-bold text-[#0B132B]">흐름을 건너, 더 나은 판단과 실행으로.</p>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">메일, 일정, 관계와 결정을 하나의 맥락으로 연결합니다.</p>
          </div>
        </aside>

        <main id="workspace-main" className="min-w-0 flex-1 overflow-hidden p-3 md:p-4">
          {children}
        </main>
      </div>

      <nav aria-label="모바일 하단 메뉴" className="grid h-16 shrink-0 grid-cols-5 border-t bg-card/95 text-[11px] font-semibold text-muted-foreground md:hidden">
        {globalNavItems.slice(0, 5).map(({ label, icon: Icon, active }) => (
          <a key={label} href={`#mobile-${label}`} aria-current={active ? 'page' : undefined} className={`flex flex-col items-center justify-center gap-1 ${active ? 'text-primary' : ''}`}>
            <Icon className="size-4" aria-hidden="true" />
            {label}
          </a>
        ))}
      </nav>
    </div>
  );
}
