# 2026-05-26 브랜딩·설정·소스 주권 Gap Closure 로드맵

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** `frontend/branding/` 디자인 근거를 저장소에 남기고, 설정
화면을 브랜딩 셸 안에서 스크롤·모바일·접근성 기준으로 실제 사용 가능한
운영 화면으로 만든 뒤, 다음 소스 주권 구현 순서를 명확히 한다.

**Architecture:** 이번 PR의 실행 slice는 설정 화면의 UI/UX 부채를 닫는다.
큰 도메인 gap인 소스별 이메일 dedupe, CalDAV/WebDAV writeback 실행,
OIDC/RBAC/ABAC 통합은 외부 provider 의존성이 있어 별도 Phase로 쪼개고,
이 문서에 검증 순서를 남긴다.

**Tech Stack:** Next.js 16, React 19, Vitest/jsdom, Playwright, FastAPI, PostgreSQL.

---

## 확인한 미구현 Gap

1. **브랜딩 원본 에셋 추적성**
   - `frontend/branding/` PNG 보드가 작업 브랜치에 없어서 PR에서 디자인 출처를 확인할 수 없었다.
   - 런타임은 `frontend/public/brand/*.svg`를 쓰므로 사용자-facing 결함은
     아니지만, 브랜딩 근거와 화면 구현을 함께 리뷰해야 한다는 요청에는
     미달했다.

2. **설정 화면의 브랜딩 셸 일관성**
   - `DashboardLayout`은 `h-screen overflow-hidden` 구조라 destination page가
     자체 스크롤을 제공해야 한다.
   - 기존 `settings/page.tsx`는 긴 내용인데 page-level scroll container가
     없고, `bg-white` 카드와 긴 탭 라벨이 모바일에서 잘릴 위험이 있었다.
   - SMTP/IMAP 필드는 placeholder만 있어 입력 후 의미가 사라졌다.

3. **소스 주권 기반 이메일 dedupe/threading**
   - 현재 이메일 unique 기준은 `(user_id, organization_id, message_id)` 중심이다.
   - ZIP 반입, 계정 간 forwarding, 같은 Message-ID가 다른 mailbox/source에
     존재하는 경우를 안전하게 표현하려면 `mailbox_account`/source identity와
     canonical duplicate link가 필요하다.

4. **CalDAV/CardDAV/WebDAV writeback 실행**
   - `/api/calendar/writeback-intent`는 provider write 실행이 아니라
     intent/provenance만 만든다.
   - ETag/If-Match, source capability, WebDAV folder organization,
     Naruon CalDAV endpoint는 다음 Phase다.

5. **Enterprise auth와 universal RBAC/ABAC**
   - 현재 signed HMAC session은 개발·초기 운영 경계다.
   - Keycloak/Casdoor OIDC, Traefik forward-auth,
     data-region/consent/customer-policy deny precedence의 API 적용은 후속
     Phase다.

## 이번 PR 구현 Task

### Task 1: 브랜딩 에셋을 저장소에 포함

**Files:**

- Add: `frontend/branding/**`

- [x] **Step 1: 브랜딩 원본 확인**

Run: `git status --short frontend/branding`

Expected: `?? frontend/branding/`

- [x] **Step 2: PNG 에셋만 포함**

Run: `git ls-files --others --exclude-standard frontend/branding`

Expected: `brand_assets/*.png`, `uiux/*.png`, `naruon_branding.png`만 staging 후보.

### Task 2: 설정 화면 scroll/accessibility RED test

**Files:**

- Create: `frontend/src/app/settings/page.test.tsx`
- Modify: `frontend/src/app/settings/page.tsx`

- [x] **Step 1: 실패하는 테스트 작성**

Test asserts:

```tsx
expect(pageShell?.className).toContain("overflow-y-auto");
expect(tabList?.className).toContain("h-auto");
expect(card.className).toContain("bg-card");
expect(container.textContent).toContain("SMTP 서버");
expect(container.textContent).toContain("IMAP 서버");
```

- [x] **Step 2: RED 확인**

Run: `npm test -- src/app/settings/page.test.tsx`

Expected: `data-testid="settings-page-scroll"` 없음으로 FAIL.

- [x] **Step 3: 최소 구현**

Implement:

```tsx
<div data-testid="settings-page-scroll" className="max-h-full overflow-y-auto ...">
<TabsList data-testid="settings-tab-list" className="h-auto overflow-x-auto ...">
<section data-testid="settings-card" className="bg-card ...">
<AccountField label="SMTP 서버"><Input ... /></AccountField>
```

- [x] **Step 4: GREEN 확인**

Run: `npm test -- src/app/settings/page.test.tsx`

Expected: PASS.

## 다음 Phase 구현 순서

1. **Mailbox source identity**
   - Backend RED: 같은 `Message-ID`가 서로 다른 mailbox/source에 들어오면
     두 source-scoped message로 남고, 같은 source 내 중복은 canonical
     duplicate로 링크된다.
   - DB object/column naming: 새 객체는 `mailbox_account`, `message_source`,
     `duplicate_link`처럼 두 단어 이상 `snake_case`를 쓴다.

2. **Sent reply tracking + ticket state transition**
   - `/api/emails/send`가 simulated/real send 결과를 ticket reply-wait 상태와 연결한다.
   - Task API는 공개 id를 유지하고 source email/thread provenance를 보존한다.

3. **CalDAV/WebDAV source registry and writeback executor**
   - Source capability, ETag/If-Match, conflict result, audit event를 저장한다.
   - Naruon 자체 저장만으로 완료 처리하지 않고 customer-owned source에 writeback한다.

4. **Self-hosted connector production artifact**
   - GitHub self-hosted runner와 구분되는 outbound-only connector package를 만든다.
   - Private IMAP/SMTP/CalDAV/CardDAV/WebDAV 접근은 connector에서만 수행한다.

5. **Enterprise identity and policy enforcement**
   - Keycloak 우선, Casdoor 대안, Traefik forward-auth 평가를 실제 JWT/JWKS 검증과 연결한다.
   - `access_policy` evaluator를 API resource checks에 적용한다.

## 검증 명령

```bash
git rev-parse --show-toplevel
(cd frontend && npm test -- src/app/settings/page.test.tsx src/components/DashboardLayout.test.tsx)
(cd frontend && npm run test:e2e -- tests/e2e/dashboard-branding.spec.ts --workers=1)
```

Playwright screenshot artifacts to inspect:

- `startup-desktop.png`
- `startup-tablet.png`
- `startup-mobile.png`
- `startup-mobile-drawer.png`
- `mobile-workspace-menu.png`
