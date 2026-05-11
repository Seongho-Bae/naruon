# Authentication and Key Management

## 확인된 사실 / Confirmed

- `backend/api/auth.py` is dummy header auth using `X-User-Id` and defaults to
  `default`.
- `backend/db/models.py` stores OAuth/OpenAI secret fields through an
  `EncryptedString` type backed by Fernet.
- `backend/db/models.py` also has a fallback Fernet key when `ENCRYPTION_KEY` is
  not configured, so production key management is not complete.
- Email rows do not yet have a mailbox ownership key, as documented in
  `ARCHITECTURE.md`.

## 가설 / Hypothesis

- Keycloak and Casdoor should be evaluated as OIDC providers after mailbox
  ownership is modeled and before production multi-user access is claimed.
- Production should require explicit `ENCRYPTION_KEY`, key rotation runbooks, and
  separate secret scopes for OpenAI, SMTP/IMAP, OAuth, and CI tokens.

## 다음 결정

- Compare Keycloak and Casdoor on OIDC support, operational complexity, admin UX,
  self-hosting footprint, backup/restore, and integration with gateway auth.
- Replace dummy auth only after tests prove every email/search/query path is
  scoped to the authenticated mailbox owner.
