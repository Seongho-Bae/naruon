# Authentication and Key Management

## 확인된 사실 / Confirmed

- `backend/api/auth.py` no longer accepts public `X-User-*`,
  `X-Organization-*`, `X-Group-*`, or `X-Dev-Auth-Token` headers as runtime
  authentication material.
- Runtime authentication accepts only `Authorization: Bearer` session envelopes
  signed with HMAC-SHA256 by the configured `AUTH_SESSION_HMAC_SECRET`. The
  secret must be explicitly configured, high-entropy generated material, and at
  least 32 bytes; missing or weak secrets fail closed with
  `401 Authentication required`.
- The signed session payload is versioned and must include
  `iss=naruon-control-plane`, `aud=naruon-api`, `sub`, explicit `role`,
  `workspace`, `exp`, and organization/group scope claims. Tampered, expired,
  malformed, wrong-secret, or invalid-role tokens are rejected; user ids such as
  `admin` do not grant privileges unless the signed role claim is elevated.
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
- Email rows now have a nullable `user_id` owner key, and
  email/search/network graph queries are scoped to the authenticated user.
  Existing local databases receive the column and a null-row default backfill
  through `backend/scripts/bootstrap_db.py`; production still needs an audited
  mailbox-owner migration/backfill before multi-tenant data is mixed.

## 가설 / Hypothesis

- Keycloak and Casdoor should be evaluated as OIDC providers before production
  multi-user access is claimed. The HMAC session envelope is a narrow internal
  bridge, not the final external IdP integration.
- Production still needs key rotation runbooks and separate secret scopes for
  `AUTH_SESSION_HMAC_SECRET`, OpenAI, SMTP/IMAP, OAuth, and CI tokens.

## 다음 결정

- Compare Keycloak and Casdoor on OIDC support, operational complexity, admin UX,
  self-hosting footprint, backup/restore, and integration with gateway auth.
- Replace the HMAC session bridge with verified OIDC/JWT claims while keeping
  regression tests that prove every email/search/network query path is scoped to
  the authenticated mailbox owner.
