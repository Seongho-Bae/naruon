# 2026-05-28 Security Governance Access Surface

## Verified gap

- `docs/plans/2026-05-24-north-star-master-spec.md` requires the Security GNB
  detail area to cover security dashboard, access permissions, audit logs,
  external sharing, and policy.
- `frontend/branding` contains only visual UX mockups, so implementation
  evidence must come from the current app rather than a separate written
  security spec.
- `frontend/src/components/SecurityLayout.tsx` was still static before this
  phase: policy rows, block logs, OIDC posture, audit logs, external sharing,
  and policy views were not source-backed, and three high-traffic tabs rendered
  inert "coming soon" copy.
- `DataLayout` and `SettingsLayout` already use signed APIs for WebDAV, CalDAV,
  account configuration, runner config, and observability signals. Security was
  therefore the smallest high-impact GNB/detail gap after provider onboarding.

## External best-practice inputs checked

- NIST SP 800-162 defines ABAC as access decisions based on subject, object,
  operation, and environmental attributes against policies. The implemented
  surface therefore displays organization, workspace, owner, source capability,
  consent, and region decisions instead of role-only examples.
  Source: https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=927500
- OWASP Authorization Cheat Sheet recommends least privilege, deny by default,
  permission checks on every request, ABAC/ReBAC over role-only checks, safe
  failure, and authorization test coverage. The UI now labels deny precedence and
  the backend evaluates ABAC denials before RBAC allows.
  Source: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP Logging Cheat Sheet says application security event logging should be
  consistent and useful for investigation. This phase does not expose the legacy
  unscoped `AuditLog` table directly; it surfaces scoped connector evidence and
  the API audit event name only.
  Source: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html

## Implemented slice

- Add signed private `GET /api/security/access-surface`.
- Return source-linked rows from:
  - `webdav_accounts`
  - `calendar_writeback_sources`
  - `connector_signal_events`
- Reuse `services.access_policy.evaluate_access` for source decisions and
  canonical deny-precedence checks.
- Keep the response read-only and explicit:
  `provider_write_executed=false`, no credential fields, no sequential
  `account_id`, no raw provider secret, no fake security claims.
- Wire Security tabs to the API:
  - dashboard summary
  - source-linked access table
  - scoped connector/audit evidence
  - external writeback boundary reviews
  - deny-first policy order and decision table

## Follow-up roadmap

- Durable org/workspace-scoped audit history was split into
  `docs/plans/2026-05-29-security-durable-audit-surface.md` and implemented as
  a separate `security_audit_events` source. Do not expose the legacy unscoped
  `AuditLog` table directly.
- Add policy mutation APIs only after versioned policy objects and approval
  workflows exist.
- Add external sharing approval/revocation APIs only after provider connector
  execution can enforce source capability, consent, and ETag/If-Match checks.
