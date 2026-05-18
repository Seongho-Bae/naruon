# Authentication and Key Management

## 확인된 사실 / Confirmed

- `backend/api/auth.py` no longer accepts public `X-User-*` headers by
  themselves. The development-only header path is disabled for the default
  production runtime and requires `RUNTIME_ENVIRONMENT` to be `local`,
  `development`, or `test`, `TRUST_DEV_HEADERS=true`, plus a configured
  `DEV_AUTH_TOKEN` of at least 32 characters that matches `X-Dev-Auth-Token`.
- User IDs do not imply administrative roles. Development header auth only honors
  explicit trusted role headers after the runtime, feature flag, and token gates
  all pass.
- `backend/db/models.py` stores OAuth/OpenAI secret fields through an
  `EncryptedString` type backed by Fernet.
- `backend/db/models.py` no longer contains a fallback Fernet key. Secret-field
  encryption now requires an explicit `ENCRYPTION_KEY` in every runtime mode,
  including `DEBUG=true`. User-facing routes that touch encrypted fields should
  return the existing operator-facing missing-key error rather than fallback
  encryption.
- Email rows do not yet have a mailbox ownership key, as documented in
  `ARCHITECTURE.md`.

## 가설 / Hypothesis

- Keycloak and Casdoor should be evaluated as OIDC providers after mailbox
  ownership is modeled and before production multi-user access is claimed.
- Production still needs key rotation runbooks and separate secret scopes for
  OpenAI, SMTP/IMAP, OAuth, and CI tokens.

## 다음 결정

- Compare Keycloak and Casdoor on OIDC support, operational complexity, admin UX,
  self-hosting footprint, backup/restore, and integration with gateway auth.
- Replace development-token header auth with verified OIDC/JWT claims only after
  tests prove every email/search/query path is scoped to the authenticated
  mailbox owner.
