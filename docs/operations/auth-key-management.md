# Authentication and Key Management

## 확인된 사실 / Confirmed

- `backend/api/auth.py` no longer accepts public `X-User-*`,
  `X-Organization-*`, `X-Group-*`, or `X-Dev-Auth-Token` headers as runtime
  authentication material. The runtime auth dependency fails closed until a
  verified OIDC/JWT/session provider supplies trusted identity, role, and scope
  claims.
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
- Replace the fail-closed runtime auth placeholder with verified OIDC/JWT claims
  only after tests prove every email/search/query path is scoped to the
  authenticated mailbox owner.
