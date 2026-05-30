# 2026-05-29 Security Durable Audit Surface

## Verified gap

- `docs/plans/2026-05-28-security-governance-access-surface.md` intentionally
  avoided exposing the legacy `audit_logs` table because it lacks durable
  organization and workspace scope.
- Security tabs already read signed source evidence, but the audit tab could
  only show connector events plus the current API audit event name. LLM provider
  mutations still wrote only legacy `AuditLog` rows, so access-surface users
  could not inspect scoped provider-governance changes.
- The implementation must preserve the database naming rule for new objects:
  every new table and column uses two-word `snake_case`; no new sequential ids
  are exposed in the API.

## Implemented slice

- Add `security_audit_events` as the durable scoped audit source.
- Write `create`, `update`, and `delete` LLM provider governance events with:
  `actor_user_id`, `actor_role`, `organization_id`, `workspace_id`,
  `event_action`, `resource_type`, `resource_uid`, `evidence_source`,
  `detail_text`, and `observed_at`.
- Keep durable LLM provider audit details generic and use scoped opaque
  `resource_uid` values so accidental secret-like provider names are not copied
  into the Security API or UI.
- Bootstrap fresh and existing PostgreSQL databases with the table and scoped
  indexes:
  - `ix_security_audit_events_scope_time`
  - `ix_security_audit_events_actor_scope`
- Extend signed `GET /api/security/access-surface` to return
  `durable_audit_events`.
- Scope reads by signed context:
  - organization admins see events in their organization and workspace;
  - members see only their own actor events in their organization/workspace.
- Keep legacy `AuditLog` as an internal compatibility sink only; it is not
  returned by the Security API or UI.
- Render durable audit evidence in the Security audit tab with event UID,
  actor, workspace, resource UID, evidence source, observed time, and detail
  text. Connector evidence remains separate.

## Verification

- Backend fast tests cover:
  - `security_audit_events` naming and indexes;
  - bootstrap SQL table/index creation;
  - LLM provider CRUD writing three scoped durable audit events without API key
    leakage;
  - Security access-surface org/member filtering and redaction.
- PostgreSQL smoke paths cover bootstrap/access behavior when a local test
  database is available.
- Frontend unit tests cover signed-session fetch headers and audit-tab rendering
  of both durable audit and connector evidence.
- Browser verification must still capture desktop, tablet, and mobile Security
  screenshots before PR merge evidence is complete.

## Remaining roadmap

- Add versioned policy mutation and approval workflows before exposing write
  controls from the policy tab.
- Add external sharing approval/revocation APIs only after provider connector
  execution can enforce source capability, consent, and ETag/If-Match checks.
