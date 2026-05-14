# Authentication and Key Management

## 확인된 사실 / Confirmed

- `backend/api/auth.py` now supports `AUTH_MODE=header|hybrid|oidc`.
- Default backend auth is fail-closed (`AUTH_MODE=hybrid`); trusted header auth
  now requires explicit `DEBUG=true` or `TRUST_DEV_HEADERS=true`.
- `docker-compose.yml` and `docker-compose.live-e2e.yml` default to fail-closed
  auth (`AUTH_MODE=hybrid`, `TRUST_DEV_HEADERS=false`). Localhost development or
  live-E2E runs that need the trusted-header identity shim must set
  `AUTH_MODE=header` and `TRUST_DEV_HEADERS=true` explicitly, and the published
  ports stay bound to `127.0.0.1` so that escape hatch remains loopback-local.
- In `oidc`/`hybrid`, bearer tokens are decoded into the shared `AuthContext`
  contract and map `sub`, role claims, `organization_id`, and `groups`.
- The backend accepts HS256 shared-secret tokens and RS256 bearer tokens
  validated against `OIDC_JWKS_URL`, which matches staged Keycloak/Casdoor
  rollout patterns.
- Dev header fallback is still available only when backend debug/trusted-header
  mode is enabled; frontend dev identity UI is restricted to loopback hosts
  (`localhost`, `127.0.0.1`), waits for `/api/runtime-config` to confirm the
  backend escape hatch, and disappears when a bearer token is present.
- `/api/runner-config` is organization-scoped and claim-gated to
  `platform_admin` / `organization_admin` with organization scope.
- `/api/llm-providers` is claim-gated and now persists `organization_id`, with
  `(organization_id, name)` as the uniqueness boundary.
- `/api/prompts` keeps private prompts user-owned, while shared prompt templates
  require an authenticated `organization_id` and are listed only within that
  organization.
- `/api/execution-items` is a self-owned personal queue only. It now requires
  the source email row to belong to the authenticated user's `Email.user_id`
  scope, and the queue itself is isolated by `user_id + workspace_id`.
- `/api/mailbox-accounts` accepts user-owned SMTP/IMAP/POP3 account settings but
  rejects loopback, private, link-local, metadata, resolved-private, and
  non-mail ports before persistence to prevent mailbox setup from becoming an
  internal network probe.
- Legacy `llm_providers.organization_id IS NULL` rows are not auto-rewritten on
  startup anymore. Operators must opt into the one-off bootstrap mapping with
  `LEGACY_LLM_PROVIDER_ORGANIZATION_ID=<org-id>` or run an equivalent explicit
  migration.
- `backend/db/models.py` stores OAuth/OpenAI secret fields through an
  `EncryptedString` type backed by Fernet.
- `backend/db/models.py` also has a fallback Fernet key when `ENCRYPTION_KEY` is
  not configured, so production key management is not complete.
- Email rows now have a minimal owner key (`Email.user_id`), but that is only a
  bridge toward a real `Mailbox` aggregate and does not yet encode provider /
  account provenance.
- Mailbox-filtered search/thread reads temporarily include authenticated-owner
  legacy rows with `mailbox_account_id IS NULL`; the frontend labels them as
  `이전 복원 메일` during the bridge period instead of presenting them as native
  rows from the selected mailbox.
- Legacy rows are only backfilled when operators explicitly set
  `LEGACY_EMAIL_OWNER_USER_ID`. The example env now leaves it blank on purpose,
  manual import/restore scripts refuse to proceed without an explicit owner, and
  bootstrap fails closed if ownerless email rows still exist without that mapping.
- `/api/calendar/sync` now requires authenticated app identity, ignores any
  submitted body `user_token`, and returns 503 until server-side per-user Google
  Calendar credentials are available.

## 가설 / Hypothesis

- Keycloak and Casdoor can now be integrated incrementally through RS256/JWKS
  bearer validation without waiting for a gateway-only rollout.
- Full production multi-user claims still depend on mailbox ownership and
  tenant-scoped email/search persistence, as documented in `ARCHITECTURE.md`.
- Production should require explicit `ENCRYPTION_KEY`, key rotation runbooks, and
  separate secret scopes for OpenAI, SMTP/IMAP, OAuth, and CI tokens.

## 다음 결정

- Compare Keycloak and Casdoor on OIDC support, operational complexity, admin UX,
  self-hosting footprint, backup/restore, and integration with gateway auth.
- Replace the temporary legacy-provider bootstrap mapping with a real migration
  runbook that can safely map rows per organization instead of one env-scoped
  fallback value.
- Document and eventually replace `LEGACY_EMAIL_OWNER_USER_ID` with a real
  mailbox/account migration path instead of a one-shot owner backfill.
- Replace the remaining header-only/dev assumptions only after tests prove every
  email/search/query path is scoped to the authenticated mailbox owner.
