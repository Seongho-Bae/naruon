'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React, { useState } from 'react';
import {
  CalendarDays,
  CheckCircle2,
  FileText,
  HelpCircle,
  Home,
  Inbox,
  Menu,
  Network,
  PenLine,
  Search,
  Send,
  Sparkles,
  Star,
  Target,
  FolderOpen,
  TrendingUp,
  Edit3
} from 'lucide-react';

const mailNavItems = [
  { label: '받은 메일', description: '우선순위 인박스', icon: Inbox, href: '/' },
  { label: '중요 메일', description: '중요 표시된 메일', icon: Star, href: '/starred' },
  { label: '보낸 메일', description: '발송 완료', icon: Send, href: '/sent' },
  { label: '임시 보관함', description: '작성 중인 메일', icon: FileText, href: '/drafts' },
  { label: '전체 메일', description: '모든 메일함', icon: Home, href: '/all' },
];

const aiHubItems = [
  { label: '맥락 종합', description: '분산된 흐름 통합', icon: Network, href: '/ai-hub/context' },
  { label: '판단 포인트', description: '주요 의사결정 요인', icon: Target, href: '/ai-hub/decisions' },
  { label: '실행 항목', description: '추출된 업무(Action Items)', icon: CheckCircle2, href: '/ai-hub/actions' },
];

const projectItems = [
  { label: '런칭 프로젝트', description: '', icon: FolderOpen, href: '/projects/launch' },
  { label: '벤더 관리', description: '', icon: FolderOpen, href: '/projects/vendor' },
  { label: '마케팅 캠페인', description: '', icon: FolderOpen, href: '/projects/marketing' },
];

const labelItems = [
  { label: '긴급', color: 'bg-red-500', href: '/labels/urgent' },
  { label: '회의', color: 'bg-yellow-500', href: '/labels/meeting' },
  { label: '계약', color: 'bg-green-500', href: '/labels/contract' },
  { label: '디자인', color: 'bg-purple-500', href: '/labels/design' },
  { label: '개발', color: 'bg-blue-500', href: '/labels/dev' },
];

const aiNavItems = [
  { label: '받은편지함', description: '메일 스레드', icon: Inbox, active: true, mobileView: 'inbox' as const },
  { label: '맥락 종합', description: '흩어진 흐름 연결', icon: Network, mobileView: 'detail' as const },
  { label: '판단 포인트', description: '의사결정 기준', icon: Target, mobileView: 'detail' as const },
  { label: '실행 항목', description: '다음 행동 추적', icon: CheckCircle2, mobileView: 'actions' as const },
  { label: '일정 연결', description: '캘린더 반영', icon: CalendarDays, mobileView: 'calendar' as const },
];

const headerActions = [
  { label: '캘린더 반영', icon: CalendarDays },
  { label: '답장 초안', icon: PenLine },
  { label: '할 일 만들기', icon: CheckCircle2 },
];




function isActivePath(pathname: string | null, href: string) {
  if (!pathname) return false;
  return href === '/'
    ? pathname === '/'
    : pathname === href || pathname.startsWith(`${href}/`);
}

function NavLink({
  label,
  description,
  icon: Icon,
  href = '#main-content',
}: {
  label: string;
  description?: string;
  href?: string;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean }>;
}) {
  const pathname = usePathname();
  const active = isActivePath(pathname, href);

  return (
    <Link
      href={href}
      aria-current={active ? 'page' : undefined}
      className={`group flex min-h-9 items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
        active
          ? 'bg-primary text-primary-foreground shadow-[0_12px_28px_rgba(37,99,255,0.24)]'
          : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-primary'
      }`}
    >
      <Icon className="size-4" aria-hidden={true} />
      <span className="flex flex-col leading-tight">
        <span className="font-semibold">{label}</span>
        <span className={`text-[11px] ${active ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
          {description}
        </span>
      </span>
    </Link>
  );
}

function HeaderStatusChip({
  label,
  icon: Icon,
}: {
  label: string;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean }>;
}) {
  return (
    <span className="inline-flex h-10 items-center gap-2 rounded-xl border border-border bg-card px-3 text-xs font-semibold text-foreground shadow-sm">
      <Icon className="size-4 text-primary" aria-hidden={true} />
      {label}
    </span>
  );
}

export function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isWorkspaceMenuOpen, setIsWorkspaceMenuOpen] = useState(false);

  return (
    <div className="relative flex h-screen overflow-hidden bg-background text-foreground">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-card focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary focus:shadow-lg focus:outline-none focus:ring-3 focus:ring-ring/40"
      >
        Skip to main content
      </a>

      <aside aria-label="Naruon workspace sidebar" className="hidden w-60 shrink-0 flex-col overflow-hidden border-r border-sidebar-border bg-sidebar/95 px-4 py-5 shadow-[8px_0_32px_rgba(15,23,42,0.04)] lg:flex">
        <div className="space-y-5">
          <div className="flex items-center gap-3">
            <Image src="/brand/naruon-logo.svg" alt="Naruon" width={150} height={40} priority style={{ width: '150px', height: '40px' }} />
          </div>
          <div className="rounded-2xl border border-primary/15 bg-primary/5 p-4 shadow-sm">
            <p className="text-sm font-bold text-foreground">흐름을 건너, 더 나은 판단과 실행으로.</p>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              이메일, 일정, 관계와 결정을 하나의 맥락으로 연결합니다.
            </p>
          </div>
        </div>

        <div data-testid="sidebar-scroll-region" className="min-h-0 flex-1 overflow-y-auto pr-1">
          <div className="px-3 pb-4 pt-6">
            <button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold rounded-lg py-2.5 px-4 flex items-center justify-center gap-2 transition-colors">
              <Edit3 className="w-4 h-4" />
              메일 작성
            </button>
          </div>

          <nav aria-label="Mail sections" className="space-y-0.5">
            {mailNavItems.map((item) => (
              <NavLink key={item.label} {...item} />
            ))}
          </nav>

          <nav aria-label="AI Hub sections" className="mt-6 space-y-0.5">
            <div className="mb-1 flex items-center justify-between px-3">
              <p className="text-[11px] font-bold text-muted-foreground">AI 허브</p>
              <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[9px] font-bold text-primary">BETA</span>
            </div>
            {aiHubItems.map((item) => (
              <NavLink key={item.label} {...item} />
            ))}
          </nav>

          <nav aria-label="Projects sections" className="mt-6 space-y-0.5">
            <div className="mb-1 flex cursor-pointer items-center justify-between rounded-md py-1 px-3 hover:bg-secondary/50">
              <p className="text-[11px] font-bold text-muted-foreground">프로젝트</p>
              <svg width="10" height="10" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-muted-foreground"><path d="M4 6H11L7.5 10.5L4 6Z" fill="currentColor"></path></svg>
            </div>
            {projectItems.map((item) => (
              <NavLink key={item.label} {...item} />
            ))}
          </nav>

          <nav aria-label="Labels sections" className="mt-6 space-y-0.5">
            <div className="mb-1 flex cursor-pointer items-center justify-between rounded-md py-1 px-3 hover:bg-secondary/50">
              <p className="text-[11px] font-bold text-muted-foreground">라벨</p>
              <svg width="10" height="10" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-muted-foreground"><path d="M7 7V2H8V7H13V8H8V13H7V8H2V7H7Z" fill="currentColor"></path></svg>
            </div>
            {labelItems.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={`group flex min-h-8 items-center gap-3 rounded-lg px-3 py-1 text-sm transition-all focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
                    active
                      ? 'bg-primary/10 font-bold text-primary'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-primary'
                  }`}
                >
                  <div className={`w-2 h-2 rounded-full ${item.color}`} />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          <div className="px-3 pb-4 pt-6">
            <div className="rounded-xl border border-border bg-secondary/30 p-3">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-[11px] font-bold text-foreground">오늘의 인사이트</p>
                <TrendingUp className="w-3 h-3 text-muted-foreground" />
              </div>
              <p className="mb-1 text-xs text-muted-foreground">업무 집중 시간</p>
              <p className="text-xs font-bold">오전 10:00 - 12:00</p>
              <div className="mt-3 flex h-12 items-end gap-1 opacity-60">
                <div className="h-[20%] w-full rounded-t-sm bg-primary/40"></div>
                <div className="h-[40%] w-full rounded-t-sm bg-primary/40"></div>
                <div className="h-[80%] w-full rounded-t-sm bg-primary/80"></div>
                <div className="h-[100%] w-full rounded-t-sm bg-primary"></div>
                <div className="h-[60%] w-full rounded-t-sm bg-primary/60"></div>
              </div>
            </div>
          </div>

          <nav aria-label="AI workspace sections" className="sr-only">
            {aiNavItems.map(({ label }) => (
              <a key={label} href="#main-content">{label}</a>
            ))}
          </nav>
        </div>

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

      <main id="main-content" className="flex min-w-0 flex-1 flex-col overflow-hidden pb-16 lg:pb-0">
        <header aria-label="Naruon workspace header" className="flex min-h-16 items-center gap-3 border-b border-border/70 bg-card/85 px-4 backdrop-blur-xl lg:px-6">
          <button
            type="button"
            aria-label="Open workspace menu"
            aria-controls="mobile-workspace-menu"
            aria-expanded={isWorkspaceMenuOpen}
            onClick={() => setIsWorkspaceMenuOpen((open) => !open)}
            className="grid size-10 place-items-center rounded-xl border border-border text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 lg:hidden"
          >
            <Menu className="size-5" aria-hidden="true" />
          </button>
          <div className="flex items-center gap-2 lg:hidden">
            <Image src="/brand/naruon-symbol.svg" alt="" width={32} height={32} aria-hidden="true" style={{ width: '32px', height: '32px' }} />
            <span className="text-lg font-black tracking-tight">Naruon</span>
          </div>
          <label className="hidden min-w-0 flex-1 items-center rounded-2xl border border-border bg-background/80 px-4 py-2 text-sm text-muted-foreground shadow-inner shadow-slate-950/[0.02] md:flex">
            <Search className="mr-2 size-4 text-primary" aria-hidden="true" />
            <span className="sr-only">맥락 검색</span>
            <input
              className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-muted-foreground"
              placeholder="맥락, 사람, 파일, 인사이트 검색..."
              type="search"
            />
          </label>
          <div className="ml-auto hidden items-center gap-2 xl:flex">
            {headerActions.map(({ label, icon: Icon }) => (
              <HeaderStatusChip key={label} label={label} icon={Icon} />
            ))}
          </div>
          <div className="ml-auto flex items-center gap-2 xl:ml-0">
            <span aria-label="도움말 상태" className="hidden size-10 place-items-center rounded-xl border border-border text-muted-foreground md:grid">
              <HelpCircle className="size-4" aria-hidden="true" />
            </span>
            <span className="hidden rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary sm:inline-flex">
              맥락 종합
            </span>
            <span className="hidden rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700 sm:inline-flex">
              실행 중심
            </span>
          </div>
        </header>

        <section className="min-h-0 flex-1 overflow-hidden p-3 lg:p-4">
          {children}
        </section>
      </main>

      <div
        id="mobile-workspace-menu"
        hidden={!isWorkspaceMenuOpen}
        className="fixed inset-x-3 top-20 z-50 rounded-3xl border border-border bg-card/98 p-4 shadow-[0_24px_70px_rgba(15,23,42,0.18)] backdrop-blur-xl lg:hidden"
      >
        <div className="mb-3 flex items-center justify-between">
          <p className="text-sm font-black text-foreground">워크스페이스 메뉴</p>
          <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">모바일</span>
        </div>
        <nav aria-label="Mobile workspace menu" className="grid gap-2">
          {mailNavItems.map(({ label, description, icon: Icon, href }) => {
            const active = isActivePath(pathname, href);
            return (
            <Link
              key={label}
              href={href}
              aria-current={active ? 'page' : undefined}
              onClick={() => setIsWorkspaceMenuOpen(false)}
              className="flex min-h-11 items-center gap-3 rounded-2xl border border-border/70 bg-background/70 px-3 py-2 text-sm font-semibold text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
            >
              <Icon className="size-4 text-primary" aria-hidden="true" />
              <span className="flex flex-col leading-tight">
                <span>{label}</span>
                <span className="text-[11px] font-medium text-muted-foreground">{description}</span>
              </span>
            </Link>
          )})}
        </nav>
      </div>

      <nav aria-label="Mobile workspace sections" className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-4 rounded-3xl border border-border bg-card/95 p-2 shadow-[0_18px_50px_rgba(15,23,42,0.14)] backdrop-blur-xl lg:hidden">
        {mailNavItems.map(({ label, icon: Icon, href }) => {
          const active = isActivePath(pathname, href);
          return (
            <Link
              key={label}
              href={href}
              onClick={() => setIsWorkspaceMenuOpen(false)}
              data-mobile-view={label}
              aria-current={active ? 'page' : undefined}
              className={`flex min-h-11 flex-col items-center justify-center gap-1 rounded-2xl text-[11px] font-semibold text-center ${
                active ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'
              }`}
            >
              <Icon className="size-4" aria-hidden="true" />
              {label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
