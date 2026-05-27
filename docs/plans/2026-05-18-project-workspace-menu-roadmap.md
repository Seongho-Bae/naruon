# Project Workspace Menu Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the remaining project-menu dead space by turning sidebar project items into real deep links and a roadmap page grounded in branding, existing plans, and researched platform patterns.

**Architecture:** Keep this slice frontend-only and route-oriented: `/projects` exposes sections for launch, vendor, and marketing workspaces while documenting the north-star integration contracts that future backend episodes must implement. The page explicitly preserves Naruon as a relay/proxy client, not an email server, and names connector, CalDAV/CardDAV/WebDAV, RBAC/ABAC, Keycloak/Casdoor, Traefik, and OpenTelemetry responsibilities.

**Tech Stack:** Next.js 16 app router, React 19, Vitest/jsdom, Playwright responsive smoke.

---

## Evidence used

- Branding: `frontend/branding/naruon_branding.png` shows action cards for `맥락 종합`, `판단 포인트`, `실행 항목`, and primary actions `캘린더 반영`, `답장 초안`, `할 일 만들기`.
- Branding: `frontend/branding/uiux/uiux2.png` shows a GNB/sidebar system with active navigation, mobile top app bar, mobile bottom tab bar, alert/profile dropdowns, and page header patterns.
- Branding: `frontend/branding/uiux/uiux3.png` shows a desktop workspace with left navigation, project-like email list, detail panel, action cards, and related mail/calendar/document tabs.
- Existing plan: `docs/plans/2026-05-17-north-star-platform-roadmap.md` requires truthful menus, connector/writeback domains, OpenTelemetry observability, and PR automation governance.
- Research anchors:
  - SaaS IA guidance emphasizes domain objects and parent/child relationships such as workspace → account → project → task.
  - CalDAV/WebDAV conflict guidance uses ETag and If-Match to prevent silent overwrite.
  - Private-network connector patterns use outbound-only tunnels/agents from customer infrastructure.
  - Open source APM baseline uses OpenTelemetry with Prometheus, Loki, Tempo/Jaeger, and Grafana.

## Files

- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/src/components/DashboardLayout.tsx`
- Create: `frontend/src/app/projects/page.test.tsx`
- Create: `frontend/src/app/projects/page.tsx`
- Create: `docs/plans/2026-05-18-project-workspace-menu-roadmap.md`

## Tasks

- [x] RED: Update `DashboardLayout.test.tsx` to require `런칭 프로젝트`, `벤더 관리`, and `마케팅 캠페인` to be links to `/projects#launch`, `/projects#vendor`, `/projects#marketing`, not `준비 중` controls.
- [x] RED: Add `frontend/src/app/projects/page.test.tsx` requiring `/projects` to render those section IDs plus north-star integration text for CalDAV/CardDAV/WebDAV, self-hosted connector, Keycloak, Traefik, OpenTelemetry, and RBAC/ABAC.
- [x] GREEN: Update `DashboardLayout.tsx` project items to available deep links with useful descriptions.
- [x] GREEN: Implement `/projects` with project sections, action links, and north-star architecture cards.

## Acceptance

- Sidebar project items no longer contribute dead space or route to nonexistent `/projects/*` pages.
- `/projects` is usable as a menu-level planning page and does not claim Naruon is an email server.
- Page content includes connector, CalDAV/CardDAV/WebDAV writeback, RBAC/ABAC, Keycloak/Casdoor, Traefik, OpenTelemetry, and data-sovereignty language.
- Responsive tests and screenshot evidence must be added before commit.

## Verification evidence

- RED: `npm test -- src/components/DashboardLayout.test.tsx src/app/projects/page.test.tsx` failed because project sidebar items were still `준비 중` and `/projects` did not exist.
- GREEN: `npm test -- src/components/DashboardLayout.test.tsx src/app/projects/page.test.tsx` passed with 4 tests.
- Regression suite: `npm test -- src/components/DashboardLayout.test.tsx src/app/projects/page.test.tsx src/app/page.test.tsx src/components/EmailDetail.test.tsx src/app/ai-hub/page.test.tsx src/components/mobile-workspace-panels.test.tsx` passed with 39 tests.
- Static checks: `npm run typecheck` and `npm run lint` passed.
- Responsive/e2e: `LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts` passed with 16 tests, including viewport overflow and mobile hamburger composition checks.
- Browser smoke: `/projects#marketing` at 390×720 and `/projects#vendor` at 1280×900 had no horizontal overflow; `/projects#launch` screenshot captured as `projects-workspace-1280.png`.
