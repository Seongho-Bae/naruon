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
  Settings,
  Code,
  Star,
  Target,
} from 'lucide-react';

const mailNavItems = [
  { label: '받은 메일', description: '우선순위 인박스', icon: Inbox, href: '/' },
  { label: 'AI Hub', description: '최근 요약 및 인사이트', icon: Network, href: '/ai-hub' },
  { label: 'Prompt Studio', description: '프롬프트 테스트 및 관리', icon: Code, href: '/prompt-studio' },
  { label: '워크스페이스 설정', description: 'LLM 및 보안 설정', icon: Settings, href: '/settings' },
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
  description: string;
  href?: string;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean }>;
}) {
  const pathname = usePathname();
  const active = isActivePath(pathname, href);

  return (
    <Link
      href={href}
      aria-current={active ? 'page' : undefined}
      className={`group flex min-h-11 items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/40 ${
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

      <aside aria-label="Naruon workspace sidebar" className="hidden w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar/95 px-4 py-5 shadow-[8px_0_32px_rgba(15,23,42,0.04)] lg:flex">
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

        <nav aria-label="Naruon workspace sections" className="mt-6 space-y-1.5">
          <p className="px-3 text-[11px] font-bold uppercase tracking-[0.18em] text-muted-foreground">워크스페이스</p>
          {mailNavItems.map((item) => (
            <NavLink key={item.label} {...item} />
          ))}
        </nav>

        <nav aria-label="AI workspace sections" className="sr-only">
          {aiNavItems.map(({ label }) => (
            <a key={label} href="#main-content">{label}</a>
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
