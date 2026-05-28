# AGENTS.md

## Release governance defaults

- GitHub Actions used by governed workflows must be pinned to full commit SHAs
  with a trailing version comment, for example `# v6`; major-only refs such as
  `@v6` are not allowed in release or security workflows.
- Security scanners are required gates. Do not use `continue-on-error: true` to
  hide Bandit, Strix, CodeQL, or dependency findings; preserve artifacts with
  explicit `if: ${{ always() }}` upload steps when needed.
- Prefer upgrading or removing vulnerable dependencies over downgrading patched
  packages unless compatibility evidence is recorded in the PR.
- Strix Security Scan must not route through GitHub Models, `github.token`,
  generic `LLM_API_KEY`, GPT-4o, or GPT-4.1. The current organization-secret
  route is `STRIX_LLM` with `GCP_SA_KEY`; `vertex_ai/gemini-2.5-flash` is the
  validated operational model after run `26581416713` proved
  `vertex_ai/gemini-3.1-pro-preview-customtools` returns Vertex 404/no-access in
  this project. Expose Google/Vertex credentials only for Vertex provider mode.
  Direct OpenAI GPT-5.4-or-newer scans remain supported only when selected
  explicitly with `STRIX_OPENAI_API_KEY`. Do not silently fall back between
  providers, and record provider evidence in the PR. Keep architecture docs and
  reusable Strix gate tests aligned with this rule so stale GitHub Models,
  OpenAI-only, unavailable-model, or generic-key examples cannot re-enter copied
  workflow guidance.

## PR automation and review defaults

- Follow `docs/development/merge-gate-policy.md` for PR gate interpretation.
- PR Governance must stay metadata-only: no PR-head checkout, no admin merge, no
  review dismissal, and no security-check suppression.
- Pending/queued checks and pending CodeRabbit evidence are wait states, not hard
  failures. Hard blockers should be reported through the idempotent
  `<!-- pr-governance:metadata-gate -->` comment path.
- Missing current-head CodeRabbit evidence is a wait state until bounded polling
  or authoritative skip/review evidence resolves it; do not post a hard blocker
  only because the current head has not been reviewed yet.
- Keep CodeRabbit `request_changes_workflow` enabled for robot approval, but
  keep CodeRabbit GitHub Checks integration disabled. GitHub Actions are already
  evaluated by required checks and PR Governance; letting CodeRabbit also gate
  on Actions can strand a stale GitHub `CHANGES_REQUESTED` review when an
  external scanner such as direct-OpenAI Strix is quota-blocked after comments
  are fixed.
- `STARTUP_FAILURE` in required PR governance/check metadata is a hard blocker
  and should use the same idempotent metadata-gate comment path.
- Trusted-base governance materialization must tolerate transient GitHub API
  truncation such as `unexpected end of JSON input` with bounded retries and
  archive validation; do not convert that infrastructure flake into a CodeRabbit
  or review blocker.

## Workspace and task tracking defaults

- First-run frontend sessions should open the Today execution dashboard while
  preserving explicit Dashboard, Email, and Calendar startup choices.
- Workspace navigation changes must keep the desktop primary nav and the
  tablet/mobile drawer in sync for Mail, Calendar, Tasks, Projects, Context
  Search, AI Hub, Data, Security, and Settings; add route and responsive E2E
  coverage instead of documenting unavailable destinations as implemented.
- Workspace destination pages must show actionable detail surfaces, not inert
  marketing placeholders. Calendar needs month/week/detail/coordination and
  CalDAV writeback states; Tasks needs source-linked ticket boards/details;
  Search needs result/detail graph/timeline states; Projects needs decision logs;
  Data needs repository/ingestion/embedding/quality/WebDAV queues; Security and
  Settings need governance and operational control surfaces. Keep provider writes
  labeled as future work until source-backed integrations exist.
- Browser frontend writes to signed backend routes must carry the stored
  `naruon_session_token` as `Authorization: Bearer` and must not emit or forward
  public identity headers such as `X-User-Id`, `X-Organization-Id`,
  `X-Group-Id`, `X-Group-Ids`, `X-User-Role`, or `X-Dev-Auth-Token`;
  tests/mocks must exercise the signed-session path.
- JWT/session verification must reject unsupported critical headers (`crit`)
  before trusting payload claims; do not rely only on library defaults for this
  boundary.
- Private backend `/api/*` routers must be registered with the default
  `get_auth_context` signed-session dependency; only explicitly documented
  public endpoints such as `/` may omit it. Keep runtime feature/configuration
  endpoints signed-session protected; if the browser needs unauthenticated
  bootstrap data, add a narrowly scoped non-`/api` endpoint that cannot reveal
  operational feature flags or provider state.
  Prometheus `/metrics` must stay disabled by default and, when enabled, sit
  behind a trusted scrape path or reverse proxy access policy. Admin/provider
  registry endpoints must enforce role checks in addition to authentication. LLM
  provider `base_url` values must fail closed unless they are HTTPS, exact-host
  allowlisted by `ALLOWED_LLM_BASE_URL_HOSTS`, and resolve only to global
  addresses.
- Email-derived tasks must stay source-linked to the email/thread and tenant
  owner scope. Do not expose new sequential database ids through task APIs; use
  opaque public ids for user-visible ticket tasks. Task titles are plain text:
  reject HTML-like execution item markup at the backend boundary rather than
  storing user-supplied tags for later UI rendering. Parsed email display fields
  must not persist active HTML/script markup; preserve message/thread identifiers
  separately from UI-safe subject/body, address, and attachment display text.
- Home/Today dashboard reply-wait surfaces must read signed
  `/api/emails/pending-replies` data instead of inferring pending replies from
  generic inbox fixtures or static copy. Tests and E2E mocks must verify the
  stored `naruon_session_token` bearer path and must not add public identity
  headers.
- TenantConfig/provider account settings must be scoped by signed-session
  `user_id` and `organization_id`; do not query provider credentials or API keys
  by `user_id` only. Frontend Settings onboarding must use bearer-session API
  calls for account config, CalDAV/WebDAV source readiness, and runner token
  rotation, and mocks must not reintroduce public identity headers.
- Reply-wait task escalation must reuse the server-authoritative pending reply
  path, create or update source-linked `reply_sla` ticket tasks by opaque task
  id, and sanitize generated task titles from email subjects before persistence.
  Do not create duplicate reminder tasks for the same pending sent-mail message.
- Mail connection updates and workers must validate server-side SMTP, POP3,
  IMAP, and relay destinations before persistence or network connection. POP3
  credentials are required for POP3 sync;
  missing credentials must fail the sync path instead of logging a successful
  no-op. Do not place sensitive credential values, secret-derived values, or
  password-shaped field names in logs or raised exception text; use static
  non-secret labels such as "credential secret" instead.
- Settings account screens must be source-backed by signed-session APIs rather
  than static provider examples. Display only masked secret presence flags, keep
  blank secret fields out of save payloads so stored values are preserved, and
  do not reintroduce public identity headers in frontend account mocks.
- New database tables and columns must use at least two-word `snake_case` names;
  avoid single-token columns such as `id`, `title`, `status`, or `priority` on
  newly introduced objects.
- Public audit/event identifiers that may use human-readable prefixes must not
  be stored in artificially short `varchar(n)` columns; use opaque source UIDs
  that fit seeded smoke data and provider evidence without truncation.
- When reviews find public/private identifier leaks, stale API fixture shapes, or recurring bug patterns, update tests, frontend mocks, E2E mocks, README examples, architecture docs, and explicitly record the anti-pattern in `AGENTS.md` so the same bug pattern does not reappear in copied examples.
- When robot review cites an obsolete Strix provider policy, update the docs and
  tests to the current secret contract before accepting a rollback suggestion;
  do not reintroduce generic `LLM_API_KEY`, GitHub Models, or cross-provider
  credential forwarding while trying to satisfy old comments.
- When reviews find inert navigation/dead-space controls, either wire them to an
  implemented workspace route/API or remove the control; do not leave
  high-traffic drawer/sidebar entries as permanent `준비 중` copy.
- Icon-only workspace controls must carry localized `aria-label` text matching
  the visible app language; do not rely on the SVG icon alone for Calendar,
  Tasks, drawer, modal, or toolbar actions.
- Execution steps resulting in `Timeout`, `Fatal`, `Warn`, or `Denied` outputs are considered hard failures. Tests must run without these warnings to be considered passing.
- DB-affecting API slices need both mocked fast tests and a real PostgreSQL
  bootstrap/smoke path before PR merge evidence is considered complete.
- When a backend container reports missing `DATABASE_URL` or
  `AUTH_SESSION_HMAC_SECRET`, verify the runtime path injects the operator env
  through `scripts/naruon_compose.sh`, Kubernetes secrets, or an explicit
  orchestrator secret. Do not add code defaults, and do not mount or declare the
  full `~/.env` as a Compose `env_file` because unrelated local secrets may leak
  into the backend container.
- Backend container entrypoints must pass through `python scripts/start_backend.py`
  before `uvicorn` imports `main:app`. Do not reintroduce Dockerfile, Compose,
  live-E2E, or gateway commands that call `uvicorn main:app` directly and expose
  Pydantic import tracebacks for missing runtime settings.
- DAV/WebDAV/CalDAV routes are private integration surfaces unless explicitly
  documented otherwise. Register them with the default signed-session dependency,
  escape XML response fields before interpolation, and keep path values separate
  from log-safe display values.
- Self-hosted runner WebSocket routes must validate both a signed bearer session
  and a server-side WorkspaceRunnerConfig registration token before accepting the
  socket. Do not use the raw path token as identity, a log value, or the sole
  active-connection key.
- Self-hosted connector command handlers must never return placeholder or mock
  success for IMAP/SMTP execution. If no local customer-network adapter is
  configured, fail closed with `adapter_not_configured` and
  `provider_write_executed=false`; if an adapter is configured, wrap only the
  adapter's actual result in the standard runner response envelope.
- Calendar UI actions must request `/api/calendar/writeback-intent` with
  server-authoritative source selection and provenance. Do not wire browser
  actions back to legacy `/api/calendar/sync` unless a trusted backend credential
  dependency and source-owner contract are explicitly in scope.
- Calendar writeback UI must fail closed while the signed source registry is
  loading or errored; do not emit intent POSTs without a confirmed opaque
  `target_source_id`, and keep tests covering the loading/error boundary.
- Calendar and WebDAV workspaces must expose the current opaque writeback source
  as a deliberate user selection with capability and ETag/If-Match state.
  Automatic first-source fallback may initialize the control, but intent POSTs
  must use the selected opaque source and `409` responses must render as
  conflicts, not generic errors or completed writes.
- Calendar and WebDAV writeback source selection must resolve through opaque
  `source_uid` values, signed-session organization scope, and persisted
  writeback eligibility, not sequential CalDAV or WebDAV account ids.
  Missing writeback eligibility must fail closed. Browser-visible source ids
  must not reveal or be deterministically derived from account primary keys, and
  provider mutations remain future work until connector execution can enforce
  capability, consent, and ETag/If-Match checks.
- DAV/WebDAV folder and write paths must not expose sequential folder primary
  keys or claim provider write success from skeleton endpoints. Browser-visible
  project folders use opaque `folder_uid` values, and `/dav` mutation methods
  must fail closed until source, capability, credential, and ETag/If-Match
  execution exists.
- WebDAV folder listings must stay tenant-scoped by both `user_id` and signed
  session `organization_id`; do not reintroduce user-only folder queries because
  the same principal can exist in multiple B2B tenants.
- Mobile workspace drawers must lock background body scroll while open and keep
  the drawer itself scrollable; responsive E2E screenshots should cover the open
  hamburger state after scrolling the drawer.
- Self-sent knowledge extraction must first prove true self-to-self addressing,
  stay idempotent per source email, preserve email/thread provenance, and store
  only plain-text task titles. Do not create unlinked knowledge tasks from raw
  dict payloads when the source email row is unavailable.
- Self-sent knowledge WebDAV/Notes materialization requests must start from an
  opaque task uid, re-check owner and organization scope server-side, reject
  non-`self_sent_knowledge` tasks, and return intent metadata only until the
  connector/provider write path has source-backed ETag conflict handling.
- Private API services should return deterministic `error_code` values for
  expected failures; route layers must not derive HTTP status from human-readable
  message substrings.
- UI async state for repeated task/action rows must be keyed by the row's opaque
  public id so one row's loading, error, or result state cannot overwrite another
  row.
- Sender ontology and relationship DAG APIs must stay scoped to the signed
  session owner and organization. Source-backed UI panels must request
  `source_message_id` and `source_thread_id` filters instead of presenting a
  global relationship graph as if it were current-thread evidence.
- Unique email and forwarded-import dedupe must use strong scoped signals:
  normalized Message-ID, References/In-Reply-To, persisted duplicate provenance,
  or exact body/attachment fingerprints. Do not merge threads from subject-only
  `Fwd:` or `Re:` similarity, and keep duplicate cleanup intent-only until
  provenance persistence and source-backed import rewiring are implemented.
- Operational dashboards must distinguish live server-observed state from
  planned instrumentation. Show connector registration and active outbound
  runner socket state when available, but label sync lag, provider throttling,
  queue depth, and writeback conflict dashboards as pending until source-backed
  connector events exist.
- Security governance screens must be source-backed by signed
  `/api/security/access-surface` data. Do not ship static RBAC/ABAC rows, fake
  blocked-login logs, unsupported TLS/TDE claims, or permanent Security tab
  placeholders as implemented features. New Security mocks and E2E fixtures must
  preserve bearer-session calls and omit public identity headers.
- Data workspace repository, ingestion, embedding, and quality surfaces must be
  source-backed by signed `/api/data/quality-surface` data or explicitly labeled
  pending. Do not ship static ingestion logs, fake progress percentages, fake
  vector counts, unsupported embedding model names, static quality totals, or
  provider-write success claims; Data mocks and E2E fixtures must preserve the
  bearer-session call and omit public identity headers.
- Self-hosted connector APM history must be persisted as scoped control-plane
  signal events before the UI claims durable heartbeat evidence. Do not expose
  runner registration tokens, path tokens, or raw provider credentials in event
  ids, details, logs, Settings mocks, or E2E fixtures.

## Development environment and tooling defaults

- StepSecurity `harden-runner` will trigger false-positive `suspicious_file_access` lockouts on Next.js build and dev server executions (e.g., `router_init.js` checksum matches). Configure `disable-file-monitoring: true` in the `harden-runner` step rather than disabling the workflow or using `continue-on-error`.
- Next.js 15+ Turbopack resolves workspace roots by scanning upward for `package-lock.json`. Do not create or leave a `package-lock.json` in the user's home directory (`~/`), as it will cause Turbopack to spawn infinite background worker node processes attempting to compile the entire home directory.
- `pydantic-settings` strictly rejects unexpected environment variables by default. When sharing a common `.env` file between frontend and backend services, you must explicitly set `extra="ignore"` in the `SettingsConfigDict` to prevent fatal startup crashes.
- Backend startup must not add code defaults for `DATABASE_URL` or
  `AUTH_SESSION_HMAC_SECRET`. Support explicit env files from the operator,
  repository root, and backend working directory, and require Compose/Kubernetes
  to inject the mandatory values so missing runtime configuration fails before
  deployment rather than during `uvicorn main:app` import.
- Python standard library `re` flags (`re.IGNORECASE`) must be passed via the `flags=` keyword argument. Do not use inline `(?i)` at the start of the expression, as it will trigger `DeprecationWarning` regressions in Python 3.11+ test suites.
- Next.js builds in memory-constrained CI environments (e.g., GitHub Actions) can fail with OOM errors due to PostCSS worker explosion. Set `POSTCSS_WORKERS: "1"` and `DISABLE_POSTCSS_WORKERS: "true"` in the build environment to limit memory usage.

## Phase 10 development rules

- **Stepwise execution**: Each phase requires an atomic PR, GitHub PR Tracking, Push, and Robot Review. A phase only ends when merged. Do not proceed without merge.
- **TDD + DDD**: Practice TDD, micro TDD, nano TDD, Domain Driven Development, and Context Driven Development.
- **API Wiring**: Always work with API wiring completed.
- **Collaboration**: Respect other agents' concurrent work; do not overwrite or dismiss unfamiliar changes.
- **Subagent Delegation**: Actively delegate tasks to Subagents.
- **UI/Browser Testing**: Use a real browser for testing (do not rely on assumptions).
- **Strict Errors**: Treat `Timeout`, `Fatal`, `Warn`, and `Denied` outputs as hard failures.
- **Goal**: Actively manage tasks to ensure open PR counts converge to 0.
