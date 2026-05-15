# Dashboard Mobile RBAC Product Remediation Plan

<!-- markdownlint-disable MD013 MD036 -->
<!-- Plan keeps copy/paste commands, long requirements, and step labels. -->

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 대시보드/모바일/권한 노출을 현재 브랜치에서 작게 닫고, OIDC·합성 메일함·프로젝트/WBS·DAV·MCP 같은 제품 에픽은 별도 경계로 남긴다.

**Architecture:** 즉시 수정 가능한 Next.js shell·접근성·RBAC affordance와 FastAPI 권한 검사를 같은 slice에서 검증한다. 스키마 변경, built-in OIDC provider, mailbox aggregate, LLM runtime/router, DAV/mobile bridge, MCP execution plane은 현재 foundation 위의 후속 bounded context로 분리한다.

**Tech Stack:** Next.js App Router, React 19, Tailwind CSS, Vitest, Playwright, FastAPI, SQLAlchemy, PyJWT/JWKS, pytest.

---

## 현재 근거와 제약

- PR #200은 `613cc58c475b4f15bd06368ff923c5412500d461` 기준 checks는 green이고 CodeRabbit status도 success이지만, repository ruleset `14316398`이 `required_approving_review_count=1` 및 `require_last_push_approval=true`로 남아 GitHub merge gate가 `REVIEW_REQUIRED`를 반환한다.
- repo policy의 default merge source는 current-head CodeRabbit evidence이며 human review 대기는 기본값이 아니다. 단, `--admin` bypass는 명시 요청 없이 사용하지 않는다.
- 기존 `2026-05-14-dashboard-rbac-mobile-oidc-remediation.md`는 넓은 감사 계획이다. 이 문서는 실제로 닫을 작은 slice와 후속 에픽 경계를 다시 고정한다.
- 디자인 원본은 `/home/seongho/ai_email_client/frontend/branding/uiux/`이고, 사용자-facing copy는 AI 자체보다 맥락 종합, 판단 포인트, 실행 항목을 앞세운다.

## Scope and non-goals

### 이번 slice

1. `DashboardLayout` 모바일 drawer를 dialog로 만들고, backdrop, Escape, outside click, focus return, scroll reachability를 검증한다.
2. `AI Hub` 접근성 label과 metadata copy를 워크스페이스/맥락 중심으로 바꾼다. URL `/ai-hub/*`는 유지한다.
3. Prompt Studio를 admin-like surface로 분류한다. frontend nav/direct route와 backend prompt-sharing/provider-backed test API를 fail-closed로 맞춘다.
4. dev auth UI와 API client의 localhost-only·runtime-config-gated 동작을 일치시킨다.

### 이번 slice의 non-goals

- `/ai-hub/*` route rename.
- full `Mailbox` aggregate migration.
- platform admin org selector 설계.
- built-in Keycloak/Casdoor OIDC provider 도입.
- synthetic mailbox, project/WBS promotion, attachment semantic layer, jargon disambiguation, DAV/mobile bridge, MCP execution plane 구현.

## Task 1: Dashboard shell and mobile dialog affordance

**Files:**

- Modify: `frontend/src/components/DashboardLayout.tsx`
- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/app/layout.test.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`

**Step 1: Write failing tests**

- Assert desktop workspace nav uses `워크스페이스 맥락 메뉴` instead of `AI Hub sections`.
- Assert mobile drawer has `role="dialog"`, `aria-modal="true"`, labelled title, backdrop, Escape close, backdrop/outside close, link close, and focus return to the opener.
- Assert app metadata says `Naruon | 메일 워크스페이스` and describes 이메일·일정·관계·판단 포인트.

**Step 2: Run targeted tests to verify failure**

Run: `cd frontend && npx vitest run src/components/DashboardLayout.test.tsx src/app/layout.test.tsx`
Expected: FAIL before implementation.

**Step 3: Implement minimal code**

- Add `menuButtonRef` and `drawerRef`.
- Render a `data-testid="mobile-workspace-backdrop"` backdrop at `z-40` below the drawer.
- Add `role="dialog"`, `aria-modal="true"`, `aria-labelledby="mobile-workspace-menu-title"`.
- Close on Escape, backdrop click, outside pointer down, route link click, and return focus to the menu button.
- Keep sidebar and main scroll contracts unchanged except moving all related quick links into reachable scroll regions if tests expose clipping.

**Step 4: Verify green**

Run: `cd frontend && npx vitest run src/components/DashboardLayout.test.tsx src/app/layout.test.tsx`
Expected: PASS.

## Task 2: Prompt Studio and dev-auth RBAC hardening

**Files:**

- Modify: `frontend/src/lib/api-client.ts`
- Modify: `frontend/src/lib/api-client.test.ts`
- Modify: `frontend/src/components/DevAuthSwitcher.tsx`
- Modify: `frontend/src/app/prompt-studio/page.tsx`
- Create: `frontend/src/app/prompt-studio/page.test.tsx`
- Modify: `frontend/src/components/DashboardLayout.tsx`
- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `backend/api/prompts.py`
- Modify: `backend/tests/test_prompts_api.py`

**Step 1: Write failing tests**

- `ApiClient.canManageWorkspaceSettings()` is false for local `admin` before runtime dev-header auth is loaded/enabled.
- `DevAuthSwitcher` is hidden on `192.168.*` even when runtime config enables dev headers.
- member direct visit to Prompt Studio sees a blocked state and no save/test controls.
- organization/platform admin sees Prompt Studio controls.
- backend member cannot create `is_shared=true` prompts.
- backend member cannot call `/api/prompts/test` against organization provider.

**Step 2: Run targeted tests to verify failure**

Run:

```bash
cd frontend && npx vitest run src/lib/api-client.test.ts src/components/DashboardLayout.test.tsx src/app/prompt-studio/page.test.tsx
cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_prompts_api.py -q
```

Expected: FAIL before implementation.

**Step 3: Implement minimal code**

- Add a single frontend capability helper path: admin affordances require bearer claims with org scope or runtime-enabled localhost dev headers.
- Remove private LAN dev-auth visibility from `DevAuthSwitcher`.
- Hide Prompt Studio nav for non-admin users and render direct-route blocked state.
- Backend require `platform_admin` or `organization_admin` for shared prompts and provider-backed prompt tests.
- Preserve member-owned private prompts.

**Step 4: Verify green**

Run the same targeted frontend/backend commands. Expected: PASS with warnings as errors.

## Task 3: Product epic boundary sync

**Files:**

- Modify: `ARCHITECTURE.md`
- Modify: `docs/operations/auth-key-management.md`
- Modify: `docs/plans/2026-05-14-synthetic-mailbox-platform-program.md`

**Step 1: Update docs only after code behavior is known**

- Document Prompt Studio as admin/provider-backed until a member-safe quota/policy exists.
- Document dev header auth as localhost-only and runtime-config gated.
- Keep full production multi-user claims out of docs until `Mailbox` aggregate and org/workspace query scoping are finished.

**Step 2: Verify docs**

Run: `PYTHONPATH="${OPENCODE_HOME:-$HOME/.config/opencode}" python3 -m scripts.lint_by_filetype --json`
Expected: PASS.

## Verification matrix

| Area | Command | Expected |
|---|---|---|
| Dashboard/mobile unit | `cd frontend && npx vitest run src/components/DashboardLayout.test.tsx src/app/layout.test.tsx` | PASS |
| Frontend RBAC unit | `cd frontend && npx vitest run src/lib/api-client.test.ts src/app/prompt-studio/page.test.tsx` | PASS |
| Backend prompt RBAC | `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_prompts_api.py -q` | PASS |
| E2E branding/mobile | `cd frontend && npm run test:e2e -- tests/e2e/dashboard-branding.spec.ts` | PASS or exact local-server blocker |
| Changed-file lint | `PYTHONPATH="${OPENCODE_HOME:-$HOME/.config/opencode}" python3 -m scripts.lint_by_filetype --json` | PASS |

## Product epic boundaries

- **Mailbox aggregate:** replace bridge fields with first-class mailbox/org/workspace ownership and query scoping.
- **Synthetic multi-mailbox inbox:** merge per-account streams with provenance and dedupe policy.
- **ExecutionItem → Project/WBS:** promote email-derived action items into project/task aggregates.
- **Built-in OIDC provider/session:** Keycloak-first, Casdoor alternative, future SCIM/federation.
- **Attachment semantic layer:** parse, index, classify, and permission-check attachment-derived context.
- **Jargon disambiguation:** org/workspace glossary and per-thread term resolution.
- **LLM runtime/router:** provider selection, quota, audit, and prompt-policy enforcement.
- **DAV/mobile bridge:** CalDAV/CardDAV/WebDAV plus mobile-client operational path.
- **MCP execution plane:** tool execution contracts, approvals, audit trail, and failure isolation.

## File-level intent table

| File | Change(add/edit/delete/move) | Intent(의도) | Why(이유) | Risk/Notes |
|---|---|---|---|---|
| `frontend/src/components/DashboardLayout.tsx` | edit | 모바일 drawer와 nav affordance 정리 | 접근성·스크롤·권한 노출을 UI에서 먼저 fail-closed로 맞춤 | route rename은 하지 않음 |
| `frontend/src/lib/api-client.ts` | edit | admin capability 판정을 runtime-config gated로 통일 | dev header가 꺼져 있는데 admin UI가 먼저 열리는 문제 차단 | bearer claim path 보존 |
| `frontend/src/components/DevAuthSwitcher.tsx` | edit | localhost-only dev auth 표시 | 192.168 LAN에서 switcher만 보이고 header는 안 보내는 불일치 제거 | LAN dev flow가 필요하면 별도 설계 필요 |
| `frontend/src/app/prompt-studio/page.tsx` | edit | direct route 권한 차단 | provider-backed prompt test는 org secret을 소비하므로 admin-only | member private prompt draft는 backend에서 유지 |
| `backend/api/prompts.py` | edit | shared prompt/test API admin guard | BYOK provider와 prompt sharing의 권한 경계를 backend에서 강제 | 기존 member private prompt CRUD 보존 |
| `ARCHITECTURE.md` | edit | 현재 권한/에픽 경계 동기화 | foundation과 future epic을 혼동하지 않게 함 | 구현 이후 사실만 기록 |
