# Authentication and Key Management

## 확인된 사실 / Confirmed

- `backend/api/auth.py` no longer accepts public `X-User-*`,
  `X-Organization-*`, `X-Group-*`, or `X-Dev-Auth-Token` headers as runtime
  authentication material.
- Runtime authentication accepts only `Authorization: Bearer` compact session
  envelopes whose protected header pins `alg=HS256` and whose `header.payload`
  signing input is signed with HMAC-SHA256 by the configured
  `AUTH_SESSION_HMAC_SECRET`. The secret must be explicitly configured,
  high-entropy generated material, and at least 32 bytes; missing or weak
  secrets fail closed with `401 Authentication required`.
- The signed session payload is versioned and must include
  `iss=naruon-control-plane`, `aud=naruon-api`, `sub`, explicit `role`,
  `workspace`, `exp`, and organization/group scope claims. Tampered, expired,
  malformed, wrong-secret, wrong-algorithm, legacy two-segment, or invalid-role
  tokens are rejected; user ids such as `admin` do not grant privileges unless
  the signed role claim is elevated.
- Token issuers must mint the compact `header.payload.signature` form before this
  verifier rolls out, or the rollout must intentionally expire all legacy
  two-segment sessions.
- Endpoint tests that need fixture identity use explicit FastAPI dependency
  overrides in `backend/tests/conftest.py`; those test overrides are not the
  production auth path.
- `backend/db/models.py` stores OAuth/OpenAI secret fields through an
  `EncryptedString` type backed by Fernet.
- `backend/db/models.py` no longer contains a fallback Fernet key. Secret-field
  encryption now requires an explicit `ENCRYPTION_KEY` in every runtime mode,
  including `DEBUG=true`. User-facing routes that touch encrypted fields should
  return the existing operator-facing missing-key error rather than fallback
  encryption.
- Email rows now have nullable `user_id` and `organization_id` owner keys, and
  email/search/network graph queries are scoped to the authenticated user plus
  organization. Existing local databases receive the columns and null-row
  default backfills through `backend/scripts/bootstrap_db.py`; production still
  needs an audited mailbox-owner and organization migration/backfill before
  multi-tenant data is mixed.
- Email `message_id` uniqueness, fixture import upserts, and reply-thread lookup
  are scoped by `user_id` plus `organization_id` so reused RFC Message-ID values
  cannot cross tenant boundaries.
- `DATABASE_URL` has no code default. Every runtime, test harness, and deployment
  path must inject the database URL explicitly instead of relying on a shared
  development credential fallback.
- Tenant SMTP hosts are accepted only when the operator has placed the normalized
  hostname in `ALLOWED_SMTP_HOSTS`, the port is in `ALLOWED_SMTP_PORTS`, and the
  final send-time DNS answers are globally routable. Localhost, metadata,
  private, link-local, reserved, multicast, and otherwise non-global addresses
  are rejected before the backend opens a pinned SMTP socket.

## 가설 / Hypothesis

- Keycloak and Casdoor should be evaluated as OIDC providers before production
  multi-user access is claimed. The HMAC session envelope is a narrow internal
  bridge, not the final external IdP integration.
- Production still needs key rotation runbooks and separate secret scopes for
  `AUTH_SESSION_HMAC_SECRET`, OpenAI, SMTP/IMAP, OAuth, and CI tokens.

## Universal RBAC/ABAC contract

- Roles such as SaaS admin, enterprise admin, security operator, IT operator,
  B2B2C tenant admin, B2C member, SOHO owner, and delegated support engineer are
  authorization inputs, not final decisions by themselves.
- ABAC denies for data region, mailbox/source ownership, consent, delegation
  expiry, workspace/group scope, provider capability, legal hold, and customer
  policy must take precedence over RBAC allows.
- Runtime claims must be signed and server-verifiable. Public headers from
  browsers or edge proxies are not identity material unless they are backed by a
  validated OIDC/JWT or internal signed session envelope.

## Keycloak/Casdoor decision path

- Keycloak is the default enterprise candidate when realm federation, identity
  brokering, authorization services, admin separation, and audit requirements are
  more important than footprint.
- Casdoor remains the lighter candidate when a deployment values simpler
  self-hosting, Casbin-style policy integration, and lower operational overhead.
- Either option must preserve Naruon's signed claim contract: explicit subject,
  organization, group/workspace, role, delegation, expiry, and provider/source
  ownership claims are required before production multi-user access is claimed.

## 다음 결정

- Compare Keycloak and Casdoor on OIDC support, operational complexity, admin UX,
  self-hosting footprint, backup/restore, and integration with gateway auth.
- Replace the HMAC session bridge with verified OIDC/JWT claims while keeping
  regression tests that prove every email/search/network query path is scoped to
  the authenticated mailbox owner and organization.
