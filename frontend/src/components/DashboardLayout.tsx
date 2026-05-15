'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  CalendarDays,
  CheckCircle2,
  FileText,
  HelpCircle,
  Home,
  Inbox,
  Menu,
  Network,
  Search,
  Send,
  Settings,
  Sparkles,
  Star,
  Target,
  FolderOpen,
  TrendingUp,
  Edit3
} from 'lucide-react';

import { apiClient } from '@/lib/api-client';
import { deriveWorkspaceInsights, summarizeTodayInsight, type WorkspaceInsightEmail } from '@/lib/workspace-insights';
import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';

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

const quickLinkItems = [
  { label: '맥락 종합', href: '/ai-hub/context' },
  { label: '판단 포인트', href: '/ai-hub/decisions' },
  { label: '실행 항목', href: '/ai-hub/actions' },
];

const projectItems = [
  { label: '런칭 프로젝트', description: '', icon: FolderOpen, href: '/projects?workspace=launch' },
  { label: '벤더 관리', description: '', icon: FolderOpen, href: '/projects?workspace=vendor' },
  { label: '마케팅 캠페인', description: '', icon: FolderOpen, href: '/projects?workspace=marketing' },
];

const labelItems = [
  { label: '긴급', color: 'bg-red-500', href: '/labels?label=urgent' },
  { label: '회의', color: 'bg-yellow-500', href: '/labels?label=meeting' },
  { label: '계약', color: 'bg-green-500', href: '/labels?label=contract' },
  { label: '디자인', color: 'bg-purple-500', href: '/labels?label=design' },
  { label: '개발', color: 'bg-blue-500', href: '/labels?label=dev' },
];

const mobileWorkspaceItems = [
  { label: '받은 메일', icon: Inbox, href: '/' },
  { label: '맥락 종합', icon: Network, href: '/ai-hub/context' },
  { label: '판단 포인트', icon: Target, href: '/ai-hub/decisions' },
  { label: '실행 항목', icon: CheckCircle2, href: '/ai-hub/actions' },
  { label: '설정', icon: Settings, href: '/settings' },
];

const utilityNavItems = [
  { label: 'Prompt Studio', description: '프롬프트 작성 및 테스트', icon: Sparkles, href: '/prompt-studio' },
  { label: '설정', description: '워크스페이스 및 계정 설정', icon: Settings, href: '/settings' },
];

const mobileDrawerItems = [
  { label: '메일 작성', icon: Edit3, href: '/compose' },
  ...mailNavItems,
  { label: '프로젝트', icon: FolderOpen, href: '/projects' },
  { label: '라벨', icon: FileText, href: '/labels' },
  { label: '설정', icon: Settings, href: '/settings' },
];

const aiNavItems = [
  { label: '받은편지함', description: '메일 스레드', icon: Inbox, active: true, mobileView: 'inbox' as const, href: '/' },
  { label: '맥락 종합', description: '흩어진 흐름 연결', icon: Network, mobileView: 'detail' as const, href: '/ai-hub/context' },
  { label: '판단 포인트', description: '의사결정 기준', icon: Target, mobileView: 'detail' as const, href: '/ai-hub/decisions' },
  { label: '실행 항목', description: '다음 행동 추적', icon: CheckCircle2, mobileView: 'actions' as const, href: '/ai-hub/actions' },
  { label: '일정 연결', description: '캘린더 반영', icon: CalendarDays, mobileView: 'calendar' as const, href: '#main-content' },
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
  const [insightEmails, setInsightEmails] = useState<WorkspaceInsightEmail[]>([]);
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);
  const drawerRef = useRef<HTMLDivElement | null>(null);
  const wasWorkspaceMenuOpenRef = useRef(false);
  const shouldRestoreWorkspaceMenuFocusRef = useRef(true);
  const scrollRegionRef = useRef<HTMLDivElement | null>(null);
  const sidebarStorageKey = 'naruon.sidebarScrollTop';
  const insightCounts = useMemo(() => deriveWorkspaceInsights(insightEmails), [insightEmails]);
  const insightSummary = useMemo(() => summarizeTodayInsight(insightCounts), [insightCounts]);
  const canManageWorkspaceSettings = apiClient.canManageWorkspaceSettings();
  const visibleUtilityNavItems = useMemo(
    () => utilityNavItems.filter((item) => item.href !== '/prompt-studio' || canManageWorkspaceSettings),
    [canManageWorkspaceSettings],
  );

  const closeWorkspaceMenu = useCallback((restoreFocus: boolean) => {
    shouldRestoreWorkspaceMenuFocusRef.current = restoreFocus;
    setIsWorkspaceMenuOpen(false);
  }, []);

  useEffect(() => {
    let active = true;

    const loadInsightEmails = async () => {
      try {
        const data = await apiClient.get<{ emails: WorkspaceInsightEmail[] }>('/api/emails?limit=24');
        if (!active) return;
        setInsightEmails(data.emails || []);
      } catch {
        if (!active) return;
        setInsightEmails([]);
      }
    };

    void loadInsightEmails();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const scrollRegion = scrollRegionRef.current;
    if (!scrollRegion || typeof window === 'undefined') return;

    const savedScrollTop = Number(window.sessionStorage.getItem(sidebarStorageKey) || '0');
    scrollRegion.scrollTop = Number.isFinite(savedScrollTop) ? savedScrollTop : 0;
    const animationFrame = window.requestAnimationFrame(() => {
      scrollRegion.scrollTop = Number.isFinite(savedScrollTop) ? savedScrollTop : 0;
    });

    const handleScroll = () => {
      window.sessionStorage.setItem(sidebarStorageKey, String(scrollRegion.scrollTop));
    };

    scrollRegion.addEventListener('scroll', handleScroll);
    return () => {
      window.cancelAnimationFrame(animationFrame);
      scrollRegion.removeEventListener('scroll', handleScroll);
    };
  }, [pathname]);

  useEffect(() => {
    if (!isWorkspaceMenuOpen) return;

    const drawer = drawerRef.current;
    const focusableElements = Array.from(
      drawer?.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])') ?? [],
    );
    focusableElements[0]?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeWorkspaceMenu(true);
        return;
      }
      if (event.key !== 'Tab' || focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    };

    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (drawer?.contains(target) || menuButtonRef.current?.contains(target)) return;
      closeWorkspaceMenu(true);
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('pointerdown', handlePointerDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('pointerdown', handlePointerDown);
    };
  }, [closeWorkspaceMenu, isWorkspaceMenuOpen]);

  useEffect(() => {
    if (isWorkspaceMenuOpen) {
      wasWorkspaceMenuOpenRef.current = true;
      shouldRestoreWorkspaceMenuFocusRef.current = true;
      return;
    }

    if (!wasWorkspaceMenuOpenRef.current) return;
    wasWorkspaceMenuOpenRef.current = false;
    if (shouldRestoreWorkspaceMenuFocusRef.current) {
      menuButtonRef.current?.focus();
    }
    shouldRestoreWorkspaceMenuFocusRef.current = true;
  }, [isWorkspaceMenuOpen]);

  return (
    <div className="relative flex h-screen overflow-hidden bg-background text-foreground">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-card focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary focus:shadow-lg focus:outline-none focus:ring-3 focus:ring-ring/40"
      >
        Skip to main content
      </a>

      <aside aria-label="Naruon workspace sidebar" className="hidden w-60 shrink-0 flex-col overflow-hidden border-r border-sidebar-border bg-sidebar/95 px-4 py-5 shadow-[8px_0_32px_rgba(15,23,42,0.04)] lg:flex">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Image src="/brand/naruon-logo.svg" alt="Naruon" width={150} height={40} priority style={{ width: '150px', height: '40px' }} />
          </div>
          <p className="px-1 text-xs font-medium text-muted-foreground">메일, 판단, 실행을 한 흐름으로 묶는 작업 공간</p>
        </div>

        <div ref={scrollRegionRef} data-testid="sidebar-scroll-region" className="min-h-0 flex-1 overflow-y-auto pr-1">
          <div className="px-3 pb-4 pt-6">
            <Link href="/compose" className={cn(buttonVariants({ variant: 'default' }), 'w-full rounded-lg py-2.5 px-4 font-bold')}>
              <Edit3 className="w-4 h-4" />
              메일 작성
            </Link>
          </div>

          <nav aria-label="Mail sections" className="space-y-0.5">
            {mailNavItems.map((item) => (
              <NavLink key={item.label} {...item} />
            ))}
          </nav>

          <nav aria-label="워크스페이스 맥락 메뉴" className="mt-6 space-y-0.5">
            <div className="mb-1 flex items-center justify-between px-3">
              <p className="text-[11px] font-bold text-muted-foreground">워크스페이스</p>
              <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[9px] font-bold text-primary">CONTEXT</span>
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

          <nav aria-label="Utility sections" className="mt-6 space-y-0.5">
            <div className="mb-1 flex items-center justify-between px-3">
              <p className="text-[11px] font-bold text-muted-foreground">도구</p>
            </div>
            {visibleUtilityNavItems.map((item) => (
              <NavLink key={item.label} {...item} />
            ))}
          </nav>

          <div className="px-3 pb-4 pt-6">
            <div className="rounded-xl border border-border bg-secondary/30 p-3">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-[11px] font-bold text-foreground">오늘의 인사이트</p>
                <TrendingUp className="w-3 h-3 text-muted-foreground" />
              </div>
              <p className="mb-2 text-[11px] leading-5 text-muted-foreground">{insightSummary.description}</p>
              <ul className="space-y-1.5 text-xs font-semibold text-foreground">
                {insightSummary.highlights.map((highlight) => (
                  <li key={highlight} className="flex items-center justify-between rounded-lg bg-background/70 px-2.5 py-2">
                    <span>{highlight}</span>
                    <span className="text-[10px] text-muted-foreground">메일 기준</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <nav aria-label="워크스페이스 작업면" className="sr-only">
            {aiNavItems.map(({ label, href }) => (
              <a key={label} href={href}>{label}</a>
            ))}
          </nav>
        </div>

        <div className="mt-auto rounded-2xl border border-border/80 bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Sparkles className="size-4 text-primary" aria-hidden="true" />
            빠른 이동
          </div>
          <div className="mt-3 grid gap-2">
            {quickLinkItems.map((item) => (
              <Link key={item.href} href={item.href} className="rounded-xl border border-border bg-background/80 px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:border-primary/30 hover:text-primary">
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </aside>

      <main id="main-content" className="flex min-w-0 flex-1 flex-col overflow-hidden pb-16 lg:pb-0">
        <header aria-label="Naruon workspace header" className="flex min-h-16 items-center gap-3 border-b border-border/70 bg-card/85 px-4 backdrop-blur-xl lg:px-6">
          <button
            ref={menuButtonRef}
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
          <form aria-label="Header context search" action="/ai-hub/context" method="get" role="search" className="hidden min-w-0 flex-1 items-center rounded-2xl border border-border bg-background/80 px-4 py-2 text-sm text-muted-foreground shadow-inner shadow-slate-950/[0.02] md:flex">
            <Search className="mr-2 size-4 text-primary" aria-hidden="true" />
            <label htmlFor="header-context-search" className="sr-only">맥락 검색</label>
            <input
              id="header-context-search"
              name="q"
              className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-muted-foreground"
              placeholder="맥락, 사람, 파일, 인사이트 검색..."
              type="search"
            />
          </form>
          <div className="ml-auto hidden items-center gap-2 xl:flex">
            <HeaderStatusChip label={`오늘 검토 ${insightCounts.judgmentCount}건`} icon={Target} />
            <HeaderStatusChip label={`실행 대기 ${insightCounts.actionCount}건`} icon={CheckCircle2} />
          </div>
          <div className="ml-auto flex items-center gap-2 xl:ml-0">
            <span aria-label="도움말 상태" className="hidden size-10 place-items-center rounded-xl border border-border text-muted-foreground md:grid">
              <HelpCircle className="size-4" aria-hidden="true" />
            </span>
            <span className="hidden rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary sm:inline-flex">
              우선 검토 {insightCounts.judgmentCount}
            </span>
            <span className="hidden rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700 sm:inline-flex">
              조율 필요 {insightCounts.coordinationCount}
            </span>
          </div>
        </header>

        <section className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden p-3 pb-[calc(5.5rem+env(safe-area-inset-bottom))] lg:p-4">
          {children}
        </section>
      </main>

      {isWorkspaceMenuOpen && (
        <button
          type="button"
          aria-label="Close workspace menu"
          data-testid="mobile-workspace-backdrop"
          onClick={() => closeWorkspaceMenu(true)}
          className="fixed inset-0 z-50 bg-slate-950/50 lg:hidden"
        />
      )}

      <div
        ref={drawerRef}
        id="mobile-workspace-menu"
        hidden={!isWorkspaceMenuOpen}
        role="dialog"
        aria-modal="true"
        aria-labelledby="mobile-workspace-menu-title"
        className="fixed inset-x-3 top-20 z-[60] max-h-[calc(100vh-7rem)] overflow-y-auto rounded-3xl border border-border bg-card/98 p-4 shadow-[0_24px_70px_rgba(15,23,42,0.18)] backdrop-blur-xl lg:hidden"
      >
        <div className="mb-3 flex items-center justify-between">
          <p id="mobile-workspace-menu-title" className="text-sm font-black text-foreground">워크스페이스 메뉴</p>
          <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">모바일</span>
        </div>
        <nav aria-label="Mobile workspace menu" className="grid gap-2">
          {mobileDrawerItems.map(({ label, icon: Icon, href }) => {
            const active = isActivePath(pathname, href);
            return (
            <Link
              key={label}
              href={href}
              aria-current={active ? 'page' : undefined}
              onClick={() => closeWorkspaceMenu(false)}
              className="flex min-h-11 items-center gap-3 rounded-2xl border border-border/70 bg-background/70 px-3 py-2 text-sm font-semibold text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
            >
              <Icon className="size-4 text-primary" aria-hidden="true" />
              <span>{label}</span>
            </Link>
          )})}
        </nav>
      </div>

      <nav aria-label="Mobile workspace sections" className="fixed inset-x-3 bottom-[calc(0.75rem+env(safe-area-inset-bottom))] z-40 grid grid-cols-5 rounded-3xl border border-border bg-card/95 px-2 pt-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))] shadow-[0_18px_50px_rgba(15,23,42,0.14)] backdrop-blur-xl lg:hidden">
        {mobileWorkspaceItems.map(({ label, icon: Icon, href }) => {
          const active = isActivePath(pathname, href);
          return (
            <Link
              key={label}
              href={href}
              onClick={() => closeWorkspaceMenu(false)}
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
