# Authentication and Key Management

## 확인된 사실 / Confirmed

- `backend/api/auth.py` now authenticates from verified bearer/OIDC claims only.
- Default backend auth is fail-closed (`AUTH_MODE=hybrid`). The legacy
  `AUTH_MODE=header` value remains parseable for configuration compatibility but
  no longer authenticates client-controlled identity headers.
- `DEBUG=true` and `TRUST_DEV_HEADERS=true` do not make `X-User-*` request
  headers authoritative for user, role, organization, group, or workspace scope.
- `docker-compose.yml` and `docker-compose.live-e2e.yml` default to fail-closed
  auth (`AUTH_MODE=hybrid`, `TRUST_DEV_HEADERS=false`). Localhost development or
  live-E2E runs must use signed bearer tokens or an OIDC provider/session.
- In `oidc`/`hybrid`, bearer tokens are decoded into the shared `AuthContext`
  contract and map `sub`, role claims, `organization_id`, and `groups`.
- The backend accepts HS256 shared-secret tokens and RS256 bearer tokens
  validated against `OIDC_JWKS_URL`, which matches staged Keycloak/Casdoor
  rollout patterns.
- Dev header fallback is removed from the backend request dependency. The
  frontend no longer sends `X-User-*` identity headers and the legacy dev identity
  switcher renders nothing.
- `/api/runner-config` is organization-scoped and claim-gated to
  `platform_admin` / `organization_admin` with organization scope.
- `/api/llm-providers` is claim-gated and now persists `organization_id`, with
  `(organization_id, name)` as the uniqueness boundary.
- `/api/prompts` keeps private prompts user-owned, while shared prompt templates
  require an authenticated `organization_id` plus `platform_admin` or
  `organization_admin`. Shared prompts are listed only within that organization,
  and provider-backed `/api/prompts/test` is also workspace-admin-only because it
  consumes the organization's LLM provider configuration. Prompt Studio mirrors
  that backend boundary by hiding its nav/direct controls from non-admin users.
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
- Replace the remaining test and operator assumptions with signed bearer or OIDC
  sessions as mailbox/account ownership evolves beyond the current bridge fields.
