# HMAC System Admin Boundary Roadmap

## Evidence

- Master Strix run `26641767705` reported a critical JWT authentication bypass:
  if an attacker learns `AUTH_SESSION_HMAC_SECRET`, they can forge a
  `system_admin` token.
- The runtime already validates HMAC secret length, fixture values, issuer,
  audience, expiration, role names, and unsupported critical headers.
- The remaining high-impact path is platform-wide role minting through the
  legacy HMAC fallback.

## Plan

1. Keep OIDC/JWKS verification authoritative when `OIDC_ISSUER_URL` is
   configured.
2. Reject `system_admin` and `platform_admin` role claims on the legacy HMAC
   fallback path.
3. Keep tenant-scoped HMAC sessions working for existing workspace flows.
4. Add signed bearer regression tests proving HMAC platform-admin claims fail.
5. Record the anti-pattern in `AGENTS.md` so future admin endpoints do not
   reintroduce platform-wide HMAC sessions.

## Non-Goals

- This does not remove HMAC sessions for tenant-scoped local development or
  existing non-platform workspace flows.
- This does not weaken OIDC; platform-wide roles should come from an external
  IdP or an audited support flow.
