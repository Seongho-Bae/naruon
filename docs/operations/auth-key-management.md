# Authentication and Key Management

## 확인된 사실 / Confirmed

- `backend/api/auth.py` no longer accepts public `X-User-*` headers by
  themselves. The development-only header path requires `TRUST_DEV_HEADERS=true`
  plus a configured `DEV_AUTH_TOKEN` that matches `X-Dev-Auth-Token`.
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
