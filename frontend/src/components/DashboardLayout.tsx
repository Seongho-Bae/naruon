'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React, { useState } from 'react';
import {
  Bell,
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
  MoreHorizontal,
  Settings,
  TrendingUp,
  UserCircle,
  Edit3
} from 'lucide-react';

import { setMobileWorkspaceView, useMobileWorkspaceView } from '@/lib/mobile-workspace';
import { setWorkspaceStartupView, useWorkspaceStartupView, type WorkspaceStartupView } from '@/lib/workspace-preferences';

const mailNavItems = [
  { label: '받은 메일', description: '우선순위 인박스', icon: Inbox, href: '/', available: true },
  { label: '중요 메일', description: '중요 표시된 메일', icon: Star, href: '/starred', available: false },
  { label: '보낸 메일', description: '발송 완료', icon: Send, href: '/sent', available: false },
  { label: '임시 보관함', description: '작성 중인 메일', icon: FileText, href: '/drafts', available: false },
  { label: '전체 메일', description: '모든 메일함', icon: Home, href: '/all', available: false },
];

const aiHubItems = [
  { label: '맥락 종합', description: '분산된 흐름 통합', icon: Network, href: '/ai-hub/context', available: false },
  { label: '판단 포인트', description: '주요 의사결정 요인', icon: Target, href: '/ai-hub/decisions', available: false },
  { label: '실행 항목', description: '추출된 업무(Action Items)', icon: CheckCircle2, href: '/ai-hub/actions', available: false },
];

const projectItems = [
  { label: '런칭 프로젝트', description: '', icon: FolderOpen, href: '/projects/launch', available: false },
  { label: '벤더 관리', description: '', icon: FolderOpen, href: '/projects/vendor', available: false },
  { label: '마케팅 캠페인', description: '', icon: FolderOpen, href: '/projects/marketing', available: false },
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

const mobileWorkspaceItems = [
  { label: '받은편지함', icon: Inbox, view: 'inbox' as const },
  { label: '맥락 검색', icon: Search, view: 'search' as const },
  { label: '일정', icon: CalendarDays, view: 'calendar' as const },
  { label: '더보기', icon: MoreHorizontal, view: 'actions' as const },
];

const primaryNavItems = [
  { label: '홈', href: '/', icon: Home },
  { label: 'AI 허브', href: '/ai-hub', icon: Sparkles },
  { label: '프롬프트', href: '/prompt-studio', icon: PenLine },
  { label: '설정', href: '/settings', icon: Settings },
];

const startupViewItems = [
  { label: '대시보드', view: 'dashboard' as const, description: '오늘의 실행 요약' },
  { label: '이메일', view: 'email' as const, description: '받은편지함 작업공간' },
  { label: '일정', view: 'calendar' as const, description: '캘린더 연결 먼저 보기' },
];

const mobileWorkspaceMenuItems = [
  { label: '받은편지함', description: '메일 스레드', icon: Inbox, href: '#mobile-inbox', view: 'inbox' as const },
  { label: '맥락 검색', description: '메일, 첨부, 일정, 사람 검색', icon: Search, href: '#mobile-search', view: 'search' as const },
  { label: '일정 연결', description: '캘린더 반영 후보', icon: CalendarDays, href: '#mobile-calendar', view: 'calendar' as const },
  { label: 'AI 실행', description: '관계 맥락과 실행 항목', icon: Sparkles, href: '#mobile-actions', view: 'actions' as const },
];

const headerActions = [
  { label: '캘린더 반영', action: 'calendar-sync', message: '메일 상세 패널에서 실행 항목을 캘린더에 반영합니다.', icon: CalendarDays },
  { label: '답장 초안', action: 'reply-draft', message: '메일 상세 패널에서 답장 초안을 생성합니다.', icon: PenLine },
  { label: '할 일 만들기', action: 'create-task', message: '메일 상세 패널에서 실행 항목을 할 일로 정리합니다.', icon: CheckCircle2 },
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
  available = true,
}: {
  label: string;
  description?: string;
  href?: string;
  available?: boolean;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean }>;
}) {
  const pathname = usePathname();
  const active = isActivePath(pathname, href);

  if (!available) {
    return (
      <button
        type="button"
        disabled
        data-coming-soon="true"
        className="group flex min-h-9 w-full cursor-not-allowed items-center gap-3 rounded-xl px-3 py-2 text-left text-sm text-sidebar-foreground/55"
      >
        <Icon className="size-4" aria-hidden={true} />
        <span className="flex min-w-0 flex-1 flex-col leading-tight">
          <span className="flex items-center gap-2 font-semibold">
            {label}
            <span className="rounded-full bg-muted px-1.5 py-0.5 text-[9px] font-bold text-muted-foreground">준비 중</span>
          </span>
          <span className="text-[11px] text-muted-foreground/80">{description || '곧 연결됩니다'}</span>
        </span>
      </button>
    );
  }

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

function PrimaryNavLink({
  label,
  href,
  icon: Icon,
}: {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean }>;
}) {
  const pathname = usePathname();
  const active = isActivePath(pathname, href);

  return (
    <Link
      href={href}
      aria-current={active ? 'page' : undefined}
      className={`inline-flex h-10 items-center gap-2 rounded-xl px-3 text-xs font-bold transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
        active ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-primary/10 hover:text-primary'
      }`}
    >
      <Icon className="size-4" aria-hidden={true} />
      {label}
    </Link>
  );
}

function HeaderActionButton({
  label,
  action,
  icon: Icon,
}: {
  label: string;
  action: string;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean }>;
}) {
  function handleClick() {
    window.dispatchEvent(new CustomEvent('naruon:header-action', { detail: { action } }));
  }

  return (
    <button
      type="button"
      data-header-action={action}
      popoverTarget={`header-action-${action}`}
      onClick={handleClick}
      className="inline-flex h-10 items-center gap-2 rounded-xl border border-border bg-card px-3 text-xs font-semibold text-foreground shadow-sm transition-colors hover:border-primary/30 hover:text-primary focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
    >
      <Icon className="size-4 text-primary" aria-hidden={true} />
      {label}
    </button>
  );
}

export function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isWorkspaceMenuOpen, setIsWorkspaceMenuOpen] = useState(false);
  const activeMobileView = useMobileWorkspaceView();
  const startupView = useWorkspaceStartupView();

  function closeMobileWorkspaceMenu() {
    const menu = document.getElementById('mobile-workspace-menu') as (HTMLElement & { hidePopover?: () => void }) | null;
    menu?.hidePopover?.();
    setIsWorkspaceMenuOpen(false);
  }

  function handleMobileWorkspaceChange(view: (typeof mobileWorkspaceItems)[number]['view']) {
    closeMobileWorkspaceMenu();
    setMobileWorkspaceView(view);
  }

  function handleHeaderAction(action: string) {
    window.dispatchEvent(new CustomEvent('naruon:header-action', { detail: { action } }));
  }

  function handleStartupViewChange(view: WorkspaceStartupView) {
    setWorkspaceStartupView(view);
    closeMobileWorkspaceMenu();
    if (view === 'email') {
      setMobileWorkspaceView('inbox', { updateHash: false });
    }
    if (view === 'calendar') {
      setMobileWorkspaceView('calendar', { updateHash: false });
    }
  }

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

          <nav aria-label="Naruon workspace sections" className="mt-6 space-y-0.5">
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
            {labelItems.map((item) => (
              <button
                key={item.label}
                type="button"
                disabled
                data-coming-soon="true"
                className="group flex min-h-8 w-full cursor-not-allowed items-center gap-3 rounded-lg px-3 py-1 text-left text-sm text-sidebar-foreground/55"
              >
                <div className={`h-2 w-2 rounded-full ${item.color}`} aria-hidden="true" />
                <span className="flex min-w-0 items-center gap-2">
                  {item.label}
                  <span className="rounded-full bg-muted px-1.5 py-0.5 text-[9px] font-bold text-muted-foreground">준비 중</span>
                </span>
              </button>
            ))}
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
            aria-haspopup="dialog"
            popoverTarget="mobile-workspace-menu"
            onClick={() => setIsWorkspaceMenuOpen((open) => !open)}
            className="grid size-10 place-items-center rounded-xl border border-border text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 lg:hidden"
          >
            <Menu className="size-5" aria-hidden="true" />
          </button>
          <div className="flex items-center gap-2 lg:hidden">
            <Image src="/brand/naruon-symbol.svg" alt="" width={32} height={32} aria-hidden="true" style={{ width: '32px', height: '32px' }} />
            <span className="text-lg font-black tracking-tight">Naruon</span>
          </div>
          <nav aria-label="Primary workspace navigation" className="hidden items-center gap-1 xl:flex">
            {primaryNavItems.map((item) => (
              <PrimaryNavLink key={item.href} {...item} />
            ))}
          </nav>
          <label className="hidden min-w-0 flex-1 items-center rounded-2xl border border-border bg-background/80 px-4 py-2 text-sm text-muted-foreground shadow-inner shadow-slate-950/[0.02] md:flex">
            <Search className="mr-2 size-4 text-primary" aria-hidden="true" />
            <span className="sr-only">맥락 검색</span>
            <input
              className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-muted-foreground"
              placeholder="맥락, 사람, 파일, 인사이트 검색..."
              type="search"
            />
          </label>
          <div data-testid="header-action-group" className="ml-auto hidden shrink-0 flex-wrap items-center justify-end gap-2 lg:flex">
            {headerActions.map(({ label, action, icon: Icon }) => (
              <HeaderActionButton key={action} label={label} action={action} icon={Icon} />
            ))}
            {headerActions.map(({ action, message }) => (
              <div
                key={`${action}-popover`}
                id={`header-action-${action}`}
                popover="auto"
                className="max-w-xs rounded-2xl border border-border bg-card p-4 text-sm font-semibold text-foreground shadow-[0_18px_50px_rgba(15,23,42,0.18)] backdrop:bg-transparent"
              >
                {message}
              </div>
            ))}
          </div>
          <div className="ml-auto flex items-center gap-2 xl:ml-0">
            <button type="button" aria-label="알림 보기" className="hidden size-10 place-items-center rounded-xl border border-border text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 md:grid">
              <Bell className="size-4" aria-hidden="true" />
            </button>
            <button type="button" aria-label="도움말 보기" className="hidden size-10 place-items-center rounded-xl border border-border text-muted-foreground transition-colors hover:border-primary/30 hover:text-primary focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 md:grid">
              <HelpCircle className="size-4" aria-hidden="true" />
            </button>
            <button type="button" aria-label="프로필 메뉴" className="hidden h-10 items-center gap-2 rounded-xl border border-border bg-background/80 px-3 text-xs font-bold text-foreground transition-colors hover:border-primary/30 hover:text-primary focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 sm:inline-flex">
              <UserCircle className="size-4 text-primary" aria-hidden="true" />
              Seongho
            </button>
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
        popover="auto"
        role="dialog"
        aria-label="모바일 워크스페이스 메뉴"
        data-open={isWorkspaceMenuOpen ? 'true' : 'false'}
        onToggle={(event) => setIsWorkspaceMenuOpen(event.currentTarget.matches(':popover-open'))}
        className="fixed inset-x-3 top-20 z-50 w-[calc(100vw-1.5rem)] max-w-md max-h-[calc(100dvh-7rem)] overflow-y-auto overscroll-contain rounded-3xl border border-border bg-card/98 p-4 shadow-[0_24px_70px_rgba(15,23,42,0.18)] backdrop-blur-xl lg:hidden"
      >
        <div className="mb-3 flex items-center justify-between">
          <p className="text-sm font-black text-foreground">워크스페이스 메뉴</p>
          <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">모바일</span>
        </div>
        <div className="space-y-4">
          <section aria-label="Mobile startup preference" className="space-y-2">
            <p className="px-1 text-[11px] font-black text-muted-foreground">시작 화면</p>
            <div className="grid grid-cols-3 gap-2">
              {startupViewItems.map(({ label, view, description }) => {
                const active = startupView === view;
                return (
                  <button
                    key={view}
                    type="button"
                    data-startup-view={view}
                    aria-pressed={active}
                    title={description}
                    popoverTarget="mobile-workspace-menu"
                    popoverTargetAction="hide"
                    onClick={() => handleStartupViewChange(view)}
                    className={`min-h-11 rounded-2xl border px-2 text-xs font-black focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
                      active ? 'border-primary bg-primary text-primary-foreground' : 'border-border bg-background/70 text-foreground'
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </section>

          <nav aria-label="Mobile workspace menu" className="grid gap-2">
            <p className="px-1 text-[11px] font-black text-muted-foreground">메일</p>
          {mailNavItems.map(({ label, description, icon: Icon, href, available }) => {
            const active = isActivePath(pathname, href);
            if (!available) {
              return (
                <button
                  key={label}
                  type="button"
                  disabled
                  data-coming-soon="true"
                  className="flex min-h-11 cursor-not-allowed items-center gap-3 rounded-2xl border border-border/70 bg-background/50 px-3 py-2 text-left text-sm font-semibold text-muted-foreground"
                >
                  <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
                  <span className="flex flex-col leading-tight">
                    <span>{label} <span className="text-[10px]">준비 중</span></span>
                    <span className="text-[11px] font-medium text-muted-foreground">{description}</span>
                  </span>
                </button>
              );
            }
            return (
            <Link
              key={label}
              href={href}
              aria-current={active ? 'page' : undefined}
              onClick={() => {
                closeMobileWorkspaceMenu();
                setMobileWorkspaceView('inbox');
              }}
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

          <nav aria-label="Mobile workspace destinations" className="grid gap-2">
            <p className="px-1 text-[11px] font-black text-muted-foreground">워크스페이스</p>
            {mobileWorkspaceMenuItems.map(({ label, description, icon: Icon, href, view }) => {
              const active = activeMobileView === view;
              return (
                <a
                  key={view}
                  href={href}
                  aria-current={active ? 'page' : undefined}
                  onClick={() => handleMobileWorkspaceChange(view)}
                  className={`flex min-h-11 items-center gap-3 rounded-2xl border px-3 py-2 text-sm font-semibold focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
                    active ? 'border-primary bg-primary text-primary-foreground' : 'border-border/70 bg-background/70 text-foreground'
                  }`}
                >
                  <Icon className="size-4" aria-hidden="true" />
                  <span className="flex flex-col leading-tight">
                    <span>{label}</span>
                    <span className={`text-[11px] font-medium ${active ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>{description}</span>
                  </span>
                </a>
              );
            })}
          </nav>

          <nav aria-label="Mobile utility menu" className="grid gap-2">
            <p className="px-1 text-[11px] font-black text-muted-foreground">도움</p>
            <Link
              href="/settings"
              onClick={() => closeMobileWorkspaceMenu()}
              className="flex min-h-11 items-center gap-3 rounded-2xl border border-border/70 bg-background/70 px-3 py-2 text-sm font-semibold text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
            >
              <Settings className="size-4 text-primary" aria-hidden="true" />
              <span className="flex flex-col leading-tight">
                <span>설정</span>
                <span className="text-[11px] font-medium text-muted-foreground">시작 화면과 계정 설정</span>
              </span>
            </Link>
            <button
              type="button"
              disabled
              data-coming-soon="true"
              className="flex min-h-11 cursor-not-allowed items-center gap-3 rounded-2xl border border-border/70 bg-background/50 px-3 py-2 text-left text-sm font-semibold text-muted-foreground"
            >
              <HelpCircle className="size-4" aria-hidden="true" />
              <span>도움말 <span className="text-[10px]">준비 중</span></span>
            </button>
            <button
              type="button"
              disabled
              data-coming-soon="true"
              className="flex min-h-11 cursor-not-allowed items-center gap-3 rounded-2xl border border-border/70 bg-background/50 px-3 py-2 text-left text-sm font-semibold text-muted-foreground"
            >
              <UserCircle className="size-4" aria-hidden="true" />
              <span>프로필 <span className="text-[10px]">준비 중</span></span>
            </button>
          </nav>
        </div>
      </div>

      <nav aria-label="Mobile workspace sections" className="fixed inset-x-3 bottom-3 z-[60] grid grid-cols-5 items-center rounded-3xl border border-border bg-card/95 p-2 shadow-[0_18px_50px_rgba(15,23,42,0.14)] backdrop-blur-xl lg:hidden">
        {mobileWorkspaceItems.slice(0, 2).map(({ label, icon: Icon, view }) => {
          const active = activeMobileView === view;
          return (
            <a
              href={`#mobile-${view}`}
              key={label}
              onClick={() => handleMobileWorkspaceChange(view)}
              data-mobile-view={view}
              aria-current={active ? 'page' : undefined}
              className={`flex min-h-11 flex-col items-center justify-center gap-1 rounded-2xl text-[11px] font-semibold text-center ${
                active ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'
              }`}
            >
              <Icon className="size-4" aria-hidden="true" />
              {label}
            </a>
          );
        })}
        <button
          type="button"
          aria-label="AI 빠른 실행"
          aria-haspopup="dialog"
          aria-controls="mobile-ai-action-menu"
          popoverTarget="mobile-ai-action-menu"
          className="mx-auto grid size-14 -translate-y-3 place-items-center rounded-2xl bg-primary text-primary-foreground shadow-[0_18px_38px_rgba(37,99,255,0.35)] transition-transform focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 active:translate-y-[-10px]"
        >
          <Sparkles className="size-6" aria-hidden="true" />
        </button>
        {mobileWorkspaceItems.slice(2).map(({ label, icon: Icon, view }) => {
          const active = activeMobileView === view;
          return (
            <a
              href={`#mobile-${view}`}
              key={label}
              onClick={() => handleMobileWorkspaceChange(view)}
              data-mobile-view={view}
              aria-current={active ? 'page' : undefined}
              className={`flex min-h-11 flex-col items-center justify-center gap-1 rounded-2xl text-center text-[11px] font-semibold ${
                active ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'
              }`}
            >
              <Icon className="size-4" aria-hidden="true" />
              {label}
            </a>
          );
        })}
      </nav>
      <div
        id="mobile-ai-action-menu"
        role="dialog"
        aria-label="AI 빠른 실행 메뉴"
        popover="auto"
        className="fixed inset-x-5 bottom-24 z-[70] rounded-3xl border border-border bg-card/98 p-4 shadow-[0_24px_70px_rgba(15,23,42,0.2)] backdrop:bg-transparent lg:hidden"
      >
          <div className="mb-3 flex items-center justify-between">
            <div>
              <p className="text-sm font-black text-foreground">AI 빠른 실행</p>
              <p className="mt-1 text-xs text-muted-foreground">메일 맥락을 바로 실행으로 전환합니다.</p>
            </div>
            <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-bold text-primary">Naruon AI</span>
          </div>
          <div className="grid gap-2">
            {headerActions.map(({ label, action, icon: Icon, message }) => (
              <button
                key={action}
                type="button"
                data-mobile-quick-action={action}
                popoverTarget="mobile-ai-action-menu"
                popoverTargetAction="hide"
                onClick={() => handleHeaderAction(action)}
                className="flex min-h-12 items-center gap-3 rounded-2xl border border-border/80 bg-background/80 px-3 py-2 text-left text-sm font-bold text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
              >
                <Icon className="size-4 text-primary" aria-hidden="true" />
                <span className="flex flex-col leading-tight">
                  {label}
                  <span className="text-[11px] font-medium text-muted-foreground">{message}</span>
                </span>
              </button>
            ))}
          </div>
      </div>
    </div>
  );
}
