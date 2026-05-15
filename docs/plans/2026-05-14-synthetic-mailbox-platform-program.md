# Synthetic Mailbox Platform Program Plan

<!-- markdownlint-disable MD013 -->
<!-- Plan keeps copy/paste commands and long requirement statements intact. -->

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Define the execution path for the large platform epics behind built-in OIDC, synthetic multi-mailbox aggregation, action/project/WBS modeling, semantic attachment handling, DAV/mobile sync, and multi-provider LLM orchestration.

**Architecture:** Treat this as a staged domain and platform program, not a single feature. The safe order is: tenancy and mailbox ownership first, identity and real login second, synthetic aggregation and execution modeling third, then mobile/DAV/provider/MCP extensions.

**Tech Stack:** FastAPI, PostgreSQL, Next.js, IMAP/SMTP/OAuth provider adapters, embedded Keycloak, PyJWT/JWKS, pgvector/semantic indexing, provider-neutral LLM adapters, MCP runtime.

---

## Program-level findings already established

### Delivered in this branch already

- desktop dashboard summary cards + context/judgment/execution rail
- mobile five-item bottom navigation and scroll restoration
- server-backed personal `ExecutionItem` aggregate with email-linked queueing
- compose route + honest placeholder routes for primary nav destinations
- loopback-only local compose auth escape hatch + runtime-gated localhost auth UI
- first owner-scoped email boundary via `Email.user_id`, plus owner-filtered list/detail/thread APIs
- `MailboxAccount` aggregate with multi-account personal registry, default reply account, settings UI, and send-path selection support
- `Email.mailbox_account_id` field + compose preselection for replies when the source mail already knows its mailbox account
- fixture/ZIP import paths now attempt to resolve `mailbox_account_id` from active mailbox accounts for the owner
- inbox API/UI now carry mailbox-account provenance and can filter the inbox by linked account
- mailbox-scoped search now preserves `mailbox_account_id` and respects the selected inbox account filter
- mailbox-filtered thread and search reads include authenticated-owner legacy
  `mailbox_account_id IS NULL` rows during the bridge period so restored thread
  context is not silently split before the full mailbox migration
- execution items now preserve source mailbox/account provenance and a snippet so the action board can stay mailbox-aware too
- IMAP sync foundation now enumerates active `MailboxAccount` rows instead of `TenantConfig`, preparing multi-account ingestion
- POP3 sync foundation now also enumerates active `MailboxAccount` rows, with per-account timeout/error handling and UI/API support for POP3 credentials
- mailbox account writes now normalize/sanitize fields and enforce create/update invariants (default reply implies active, server/port pair validation, duplicate-account 409, missing encryption 503)
- mobile workspace drawer now has modal-style close/focus behavior, and Prompt Studio is treated as an admin/provider-backed surface rather than a member utility

### Domain model

- `Organization / Workspace` is the billing/isolation boundary.
- `Mailbox` must become a first-class aggregate, replacing the current `TenantConfig` overloading.
- `MailThread` is the true work object, not individual mail rows.
- `ExecutionItem` must be promoted from local/UI-only queue + LLM todos into a server-backed aggregate.
- `Project / WBS` is a downstream planning layer, not the first persistence target.

### Built-in OIDC

- Embedded **Keycloak first** is the recommended built-in provider path.
- App-owned OIDC session (`/login` → `/auth/callback` → httpOnly cookie) is preferred over a gateway-only forward-auth architecture.
- External federation and later SCIM should remain phase-2/3 layers.

### LLM platform

- The repo has org-scoped provider CRUD, but runtime is still effectively OpenAI-centric.
- Prompt Studio can test prompts only for workspace admins because provider-backed
  execution consumes organization LLM configuration; member-safe prompt drafting
  or quotas need a separate policy path.
- The long-term platform needs:
  - provider registry + model catalog
  - per-task routing policy
  - RPM/TPM budgets
  - same-provider and cross-provider fallback chains
  - optional ensemble execution
  - MCP as a separate execution plane

### Mobile / sync / synthetic product boundary

- Safe MVP remains responsive web + one real mailbox per member + correct thread restore.
- DAV/native-mobile/synthetic multi-account fusion should follow mailbox ownership and reply-routing hardening.

## Epic A: Mailbox ownership and synthetic inbox foundation

**Why first:** almost every advanced request depends on mailbox ownership.

**Current state:** `Email.user_id` exists, `/api/emails` reads are owner-filtered, `ExecutionItem` queueing now requires that owner match, legacy owner backfill/import paths require explicit operator input, and `MailboxAccount` now exists as the first mailbox-configuration aggregate. The system still lacks `Email.mailbox_id`, provider/source identity on stored messages, and org/workspace-aware multi-mailbox ownership.

**Must deliver:**

1. `emails` ownership columns (`member_id` and/or `mailbox_id`)
2. `attachments` ownership inheritance
3. all email/search/network queries filtered by mailbox/member/org scope
4. deterministic duplicate and thread restore path for live sync and zip restore

**Key files likely affected:**

- `backend/db/models.py`
- `backend/api/emails.py`
- `backend/api/search.py`
- `backend/api/network.py`
- `backend/import_fixtures.py`
- `backend/services/archive.py`
- `docs/threading-contract.md`

## Epic B: Execution items, email-task matching, and project/WBS handoff

**Product rule:** 메일과 할일은 정확히 매칭되어야 하며, 메일 내용/발신인/첨부/관계 단서를 함께 사용해야 한다.

**Phased model:**

1. Promote `ExecutionItem` to backend aggregate with source email/thread refs.
2. Add multi-source evidence fields:
   - source emails
   - senders/participants
   - attachment refs
   - inferred due date / coordination type
3. Add “promote to project / WBS” action when the item exceeds simple follow-up scope.

**Boundaries:**

- execution item = email-derived operational work
- project/WBS node = explicit planning object after triage

## Epic C: Built-in OIDC login with external federation path

**Recommended path:** embedded Keycloak.

**Phase order:**

1. compose stack with `keycloak` + dedicated DB
2. seeded realm/client/groups/roles
3. frontend `/login`, `/auth/callback`, `/logout`
4. httpOnly session cookie handling
5. backend strict RS256/JWKS path + claim mapping
6. map token identity to app-owned `ScopedRoleAssignment`
7. add future external IdP federation through Keycloak broker

**Later:** SCIM provisioning bridge.

## Epic D: Synthetic multi-mailbox aggregation

**Goal:** Gmail / Outlook / iCloud / company runner mailboxes appear as one synthetic workspace, but replies and upstream updates remain account-correct.

**Phases:**

1. multiple Mailboxes per member
2. account-aware send/reply routing
3. duplicate message collapse across forwarded/copied mailboxes
4. synthetic unified inbox and task/calendar/note overlays
5. upstream redistribution/sync rules back to source accounts where supported

## Epic E: Semantic layer for emails and attachments

**Goal:** 이메일과 첨부파일 모두를 semantic layer로 처리하되, 첨부는 항상 부모 스레드와 연결된다.

**Deliverables:**

- attachment parsing pipeline
- structured attachment metadata
- semantic evidence references back to parent email/thread
- support for office docs / excel / image reasoning provenance

## Epic F: Jargon disambiguation service

**Problem:** terms like `PM` are ambiguous by community.

**Minimal direction:**

1. extract jargon candidates from email corpora
2. cluster by sender/community/recipient neighborhood
3. maintain per-community glossary hypotheses with evidence snippets
4. feed disambiguated meaning into summary/judgment/action generation

## Epic G: LLM provider control plane and runtime router

**Control plane objects:**

- `ProviderAccount`
- `ModelEndpoint`
- `RoutingPolicy`
- `RuntimeBudgetPolicy`

**Runtime layers:**

1. capability filter
2. policy selector
3. execution strategy (`single`, `fallback`, `hedged`, `ensemble`)
4. provider adapter transport

**Required provider families to design for:**

- Anthropic
- Vertex AI (API key / SA key)
- Vertex third-party models
- GitHub Copilot
- OpenAI OAuth / API key
- LiteLLM
- Gemini API
- OpenRouter
- OpenAI-compatible endpoints

## Epic H: DAV / mobile ecosystem bridge

**Goal:** derived files, schedules, notes should eventually surface into iOS/macOS-native surfaces where feasible.

**Phase order:**

1. internal canonical note/file/calendar models
2. CalDAV export/sync for events
3. WebDAV or file export bridge for documents/artifacts
4. later note sync integration where product fit is proven

## Epic I: MCP tool access plane

**Rule:** MCP is not just another model option; it is a separate execution plane.

**Needs:**

- task-scoped tool profiles
- model/tool capability compatibility map
- permission + audit logging
- deny-by-default external/network tool policy

## Epic J: Per-user landing page preference

**Low-risk later slice:**

- add per-member preference
- allow Dashboard Portal / Email / future workspace home choice
- default remains Dashboard Portal

## Recommended delivery order

1. Mailbox ownership and query scoping
2. Built-in OIDC login/session
3. ExecutionItem aggregate and email-task matching
4. Multi-mailbox account routing
5. Synthetic inbox/task/calendar overlay
6. Semantic attachment layer
7. LLM router/budget/fallback control plane
8. DAV/mobile ecosystem bridge
9. Jargon disambiguation service
10. MCP tool plane
