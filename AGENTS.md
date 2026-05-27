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
- Strix Security Scan must use an OpenAI GPT-5.4-or-newer model. Prefer GitHub
  Models with `models: read`, but verify actual inference availability, not only
  catalog presence. If the repo token cannot invoke GitHub Models GPT-5.4, use
  only an explicitly named `STRIX_OPENAI_API_KEY` direct GPT-5.4 credential rather
  than downgrading to Gemini, GPT-4o, or GPT-4.1; record the inference evidence
  in the PR. Do not repurpose generic `LLM_API_KEY` for direct OpenAI Strix
  calls, because it may hold a GitHub Models token or PAT.

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
- `STARTUP_FAILURE` in required PR governance/check metadata is a hard blocker
  and should use the same idempotent metadata-gate comment path.

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
- Self-sent knowledge extraction must first prove true self-to-self addressing,
  stay idempotent per source email, preserve email/thread provenance, and store
  only plain-text task titles. Do not create unlinked knowledge tasks from raw
  dict payloads when the source email row is unavailable.

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
