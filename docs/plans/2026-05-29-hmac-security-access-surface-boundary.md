# HMAC Security Access Surface Boundary

## Evidence

- Protected-branch Strix run `26643294848` reported a medium IDOR finding on
  `/api/security/access-surface`.
- The exploit path was a forged HMAC-signed JWT with a manipulated `workspace`
  claim. PR #306 rejected platform/system admin HMAC roles, but tenant-scoped
  HMAC workspace claims were still accepted by the security posture endpoint.

## Plan

1. Mark verified runtime sessions with their verifier: `hmac`, `oidc`, or
   dependency-override test context.
2. Keep HMAC fallback usable for non-security compatibility paths, but reject it
   for `/api/security/access-surface` because it is not authoritative
   workspace-membership evidence.
3. Preserve OIDC/JWKS as the production membership authority and preserve test
   dependency overrides for scoped security-surface fixtures.
4. Add regression coverage for forged HMAC workspace claims against the security
   surface.

## Non-goals

- Do not weaken scanner gates or classify timeout, denied, fatal, or finding
  output as passing evidence.
- Do not invent a database membership registry in this slice; that belongs to
  the broader RBAC/ABAC identity-provider integration plan.
