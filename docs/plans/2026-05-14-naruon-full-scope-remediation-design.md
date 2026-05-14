# Naruon Full-Scope Remediation Design

<!-- markdownlint-disable MD013 -->
<!-- Plan keeps copy/paste commands and long requirement statements intact. -->

## 목적

사용자가 요청한 27개 항목을 단일 화면 수정이 아니라 제품·보안·도메인 프로그램으로 정리한다. 이번 브랜치에서 이미 닫은 항목과 아직 남은 항목을 분리하고, 즉시 시정 가능한 UI/RBAC/스크롤 결함은 이 브랜치에서 고친다. OIDC 내장 공급자, synthetic mailbox, semantic layer, LLM 라우터, DAV/MCP는 안전한 선후관계를 가진 후속 에픽으로 둔다.

## 현재 근거

- `ARCHITECTURE.md`는 현재 상태를 bridge 단계로 설명한다. `Email.user_id`, `Email.mailbox_account_id`, `MailboxAccount`, `ExecutionItem`은 존재하지만 full `Mailbox` aggregate, persisted IMAP/POP/OAuth ingestion, synthetic aggregation은 아직 없다.
- `frontend/branding/uiux` 보드는 로그인, 메일, 맥락 검색, 일정/실행, 설정, 보안/RBAC, 데이터/문서, AI Hub/workflow를 모두 포함한다.
- 현재 feature worktree에는 `frontend/branding`이 없고, 원본은 repository main worktree의 untracked asset으로 남아 있다. 디자인 비교는 `/home/seongho/ai_email_client/frontend/branding/uiux`를 read-only truth source로 사용한다.
- parallel audit 결과, 즉시 시정 가능한 결함은 mobile route parity, global search dead affordance, desktop settings/prompt navigation, calendar/network/prompt RBAC gaps, mobile scroll/safe-area gaps이다.

## 접근안

### 접근 A: 디자인 전체를 한 번에 구현

- 장점: 보드와 웹의 차이를 빠르게 줄인다.
- 단점: 내장 OIDC, synthetic mailbox, LLM runtime, DAV/MCP가 모두 도메인/보안 경계 변경을 요구해 회귀 위험이 크다.

### 접근 B: 안전한 foundation slice 우선 구현

- 장점: RBAC/data leakage와 mobile usability를 먼저 닫고, 이후 대형 플랫폼 에픽이 올라갈 수 있는 경계를 만든다.
- 단점: 보드에 있는 보안/데이터/워크플로우 전체 화면은 한 PR 안에서 완성되지 않는다.

### 접근 C: 문서화만 하고 구현 보류

- 장점: 위험이 거의 없다.
- 단점: 사용자가 명시한 dead space, scroll, RBAC 접근성 결함이 계속 남는다.

## 결정

접근 B를 선택한다. 즉시 구현 slice는 “사용자가 오늘 체감하는 결함”과 “보안상 열려 있으면 안 되는 결함”에 집중한다.

1. 모바일과 데스크톱에서 주요 route가 닫히지 않게 한다.
2. 검색 affordance는 실제 context route로 이동시킨다. 구현되지 않은 전역 search API를 꾸며내지 않는다.
3. scroll/safe-area는 화면 크기와 DPI가 달라도 마지막 interactive element가 가려지지 않도록 고친다.
4. RBAC는 backend에서 먼저 막는다. UI gating은 보조 장치다.
5. AI라는 단어는 기술 표기로만 제한하고, product surface는 맥락 종합, 판단 포인트, 실행 항목 중심으로 유지한다.

## 이번 slice 설계

### UI/IA

- `DashboardLayout.tsx`
  - desktop sidebar에 설정과 프롬프트/작업 설계 진입점을 추가한다.
  - mobile drawer는 compact bottom nav가 담지 못하는 전체 route map을 제공한다.
  - mobile settings icon을 calendar icon에서 settings icon으로 교체한다.
  - header search는 submit 시 `/ai-hub/context?q=...`로 이동한다.
  - `h-screen`/fixed bottom nav 조합을 safe viewport + safe-area padding 기반으로 조정한다.

- `EmailList.tsx`
  - swipe는 유지하되 tap 가능한 “실행 목록”/“완료 처리” fallback을 추가한다.
  - `ScrollArea` caller에 `min-h-0`를 보강한다.

- `EmailDetail.tsx`
  - nested scroll area가 flex parent 안에서 실제로 줄어들 수 있도록 `min-h-0`를 보강한다.

### RBAC/security

- `backend/api/calendar.py`
  - 현재 calendar sync는 body의 `user_token`을 받으며 auth dependency가 없다. 이번 slice에서는 authenticated context를 필수화하고, body token을 제거하거나 무시하는 방향으로 fail-closed한다.
  - 서버 측 per-user Google Calendar credential store가 아직 없으므로, `AuthContext`를 Google credential처럼 넘기지 않는다. credential store가 생기기 전까지 sync는 503으로 닫힌다.

- `backend/api/network.py`
  - network graph query는 `Email.user_id == current_user`를 강제한다.

- `backend/api/prompts.py`
  - prompt test는 active provider를 organization scope로 제한한다.
  - shared prompt는 현재 global 공유다. schema migration 없이 즉시 완성하기 어려우므로 이번 slice에서는 route access와 provider leakage를 먼저 막고, org-scoped prompt sharing은 별도 에픽으로 남긴다.

### 모바일 검증

- Playwright는 최소 360x800, 375x667, 430x932, 768x1024와 device scale factor 2~3을 포함한다.
- route parity, bottom nav overlap, menu scroll, inbox/detail/settings scroll reachability를 확인한다.

## 대형 에픽 경계

1. 내장 OIDC provider: Keycloak first, Casdoor alternative. app-owned `/login` → `/auth/callback` → httpOnly cookie session이 목표다.
2. Mailbox aggregate: `MailboxAccount`는 설정 aggregate이고, 저장된 email/source/attachment/thread lineage를 표현하는 `Mailbox` aggregate가 필요하다.
3. Synthetic mailbox: Gmail/iCloud/Outlook/company runner 수집 후 중복 collapse, source-account reply routing, upstream redistribution을 지원한다.
4. Execution/WBS: `ExecutionItem`은 source emails, participants, attachments, inferred due date, evidence snippets를 갖고, 필요 시 Project/WBS로 승격된다.
5. Semantic layer: email body와 attachment를 evidence/provenance 단위로 구조화한다.
6. Jargon service: community/sender graph 기반 용어 후보와 의미 가설을 추적한다.
7. LLM runtime: provider account, model endpoint, routing policy, budget policy, execution record로 분리한다. TPM/RPM, fallback, hedged, ensemble 전략을 지원한다.
8. DAV bridge: internal calendar/file/note canonical model 이후 CalDAV/WebDAV export/sync를 붙인다.
9. MCP plane: model provider가 아니라 별도 tool execution plane으로 permission/audit/deny-by-default 정책을 둔다.
10. Landing preference: user preference로 Dashboard Portal 기본값, Inbox 등 선택지를 제공한다.

## 검증 기준

- 프론트엔드 변경: Vitest targeted tests, `npm run build`, `npm run lint`, Playwright desktop/mobile.
- 백엔드 변경: affected pytest with `PYTHONWARNINGS=error`, auth/RBAC negative tests 포함.
- Bootstrap 변경: ownerless legacy email row가 있는데 `LEGACY_EMAIL_OWNER_USER_ID`가 비어 있으면 startup에서 명시적으로 실패해야 한다.
- 경고는 실패로 취급한다.
- 문서: `ARCHITECTURE.md`와 plan docs가 runtime behavior와 불일치하면 갱신한다.
