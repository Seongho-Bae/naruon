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
- Strix Security Scan must use an explicitly named `STRIX_OPENAI_API_KEY`
  OpenAI Platform credential with an OpenAI GPT-5.4-or-newer model. Do not route
  Strix through GitHub Models, `github.token`, generic `LLM_API_KEY`, Gemini,
  Google/Vertex, GPT-4o, or GPT-4.1; record direct-provider evidence in the PR.
  Keep architecture docs and reusable Strix gate tests aligned with this rule so
  stale GitHub Models examples cannot re-enter copied workflow guidance.

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
- When reviews find public/private identifier leaks, stale API fixture shapes, or recurring bug patterns, update tests, frontend mocks, E2E mocks, README examples, architecture docs, and explicitly record the anti-pattern in `AGENTS.md` so the same bug pattern does not reappear in copied examples.
- When reviews find inert navigation/dead-space controls, either wire them to an
  implemented workspace route/API or remove the control; do not leave
  high-traffic drawer/sidebar entries as permanent `준비 중` copy.
- Execution steps resulting in `Timeout`, `Fatal`, `Warn`, or `Denied` outputs are considered hard failures. Tests must run without these warnings to be considered passing.
- DB-affecting API slices need both mocked fast tests and a real PostgreSQL
  bootstrap/smoke path before PR merge evidence is considered complete.
- DAV/WebDAV/CalDAV routes are private integration surfaces unless explicitly
  documented otherwise. Register them with the default signed-session dependency,
  escape XML response fields before interpolation, and keep path values separate
  from log-safe display values.
- Self-hosted runner WebSocket routes must validate both a signed bearer session
  and a server-side WorkspaceRunnerConfig registration token before accepting the
  socket. Do not use the raw path token as identity, a log value, or the sole
  active-connection key.
- Calendar UI actions must request `/api/calendar/writeback-intent` with
  server-authoritative source selection and provenance. Do not wire browser
  actions back to legacy `/api/calendar/sync` unless a trusted backend credential
  dependency and source-owner contract are explicitly in scope.
- Calendar writeback UI must fail closed while the signed source registry is
  loading or errored; do not emit intent POSTs without a confirmed opaque
  `target_source_id`, and keep tests covering the loading/error boundary.
- Calendar and WebDAV writeback source selection must resolve through opaque
  `source_uid` values, signed-session organization scope, and persisted
  writeback eligibility, not sequential CalDAV or WebDAV account ids.
  Missing writeback eligibility must fail closed. Browser-visible source ids
  must not reveal account primary keys, and provider mutations remain future
  work until connector execution can enforce capability, consent, and
  ETag/If-Match checks.
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
- Self-hosted connector APM history must be persisted as scoped control-plane
  signal events before the UI claims durable heartbeat evidence. Do not expose
  runner registration tokens, path tokens, or raw provider credentials in event
  ids, details, logs, Settings mocks, or E2E fixtures.

## Development environment and tooling defaults

- StepSecurity `harden-runner` will trigger false-positive `suspicious_file_access` lockouts on Next.js build and dev server executions (e.g., `router_init.js` checksum matches). Configure `disable-file-monitoring: true` in the `harden-runner` step rather than disabling the workflow or using `continue-on-error`.
- Next.js 15+ Turbopack resolves workspace roots by scanning upward for `package-lock.json`. Do not create or leave a `package-lock.json` in the user's home directory (`~/`), as it will cause Turbopack to spawn infinite background worker node processes attempting to compile the entire home directory.
- `pydantic-settings` strictly rejects unexpected environment variables by default. When sharing a common `.env` file between frontend and backend services, you must explicitly set `extra="ignore"` in the `SettingsConfigDict` to prevent fatal startup crashes.
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
