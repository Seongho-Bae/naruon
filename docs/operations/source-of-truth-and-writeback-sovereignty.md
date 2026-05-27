# Source-of-Truth and Writeback Sovereignty

## 핵심 원칙 / Core contract

- Customer-owned mail, CalDAV/CardDAV, and WebDAV systems remain the source of
  truth. Naruon indexes, summarizes, and proposes actions, but it must not become
  the only durable mailbox, calendar, contact, or file store.
- Naruon-created objects must choose an owned external account/calendar/folder or
  return an explicit no-writeback state. Local cache-only storage is not a
  sovereignty-compliant write path.
- Writeback requests must use server-authoritative source records. Client requests
  may choose a target source id, but they must not supply ownership, capability,
  credential, or region claims.
- Updates must preserve provider conflict semantics: ETag/If-Match for CalDAV and
  WebDAV, provider-specific revision ids where available, and auditable conflict
  outcomes when a remote object changed first.
- ZIP imports and forwarded mail are provenance sources, not new mailbox owners.
  Dedupe uses mailbox/source keys, Message-ID, content fingerprints, forwarded
  chain metadata, and attachment hashes to link duplicates to a canonical thread.

## Connector boundary

- Private-network protocols are reached by an outbound-only self-hosted connector
  running in the customer's network or VPC.
- The connector opens a control-plane channel to `naruon.net`; Naruon does not
  require inbound firewall holes, public MX records, or public IMAP/SMTP listener
  ports in the customer network.
- GitHub self-hosted runners remain CI smoke infrastructure. They can validate
  internal connectivity, but they are not the production relay component.

## Source registry contract

Every writeback-capable account should resolve through a server-authoritative
source registry before any provider mutation is attempted. The registry record
must include an opaque `source_id`, tenant/workspace owner scope, protocol
(`imap`, `smtp`, `pop3`, `caldav`, `carddav`, `webdav`), provider host, capability
flags, consent state, data region, connector route, credential reference, and
conflict metadata such as remote ids or ETags. Browser requests may reference
`source_id`, but must never supply ownership, credential, region, or capability
claims.

Implemented slices currently cover signed task/mail provenance, dedupe/threading
contracts, source-linked ticket tasks, self-sent knowledge capture into
idempotent ticket tasks, deterministic sender ontology action hints, generic
WebDAV writeback intent, self-sent knowledge WebDAV/Notes materialization
intent, DB-backed CalDAV intent source selection through opaque
`calendar_writeback_sources.source_uid` rows, and WebDAV intent selection through
opaque, organization-scoped `webdav_accounts.source_uid` rows with persisted
writeback eligibility. Real CalDAV/WebDAV mutation,
ETag-aware WebDAV/Notes provider execution for synthesized knowledge, POP3
runtime sync, durable reply-tracking notifications, and source-id filtered
sender graph views remain episode work and must preserve this registry
boundary.

## Policy and audit requirements

- RBAC grants are necessary but never sufficient when ABAC denies apply. Region,
  consent, workspace, group, source capability, customer policy, and
  data-residency denials take precedence over broad roles.
- A permitted `platform_admin` can cross organization and resource ownership
  boundaries in Naruon's pure access-policy evaluator, but writeback still must
  use server-authoritative source records, provider capabilities, consent, and
  conflict-aware revisions before any customer-owned system is changed.
- Every writeback intent should record `actor`, `workspace`, `source_id`,
  `protocol`, `remote_id`/`etag` where available, `action`, and conflict result.
- Observability must redact email body, secrets, provider tokens, DSNs, contact
  details, and calendar descriptions unless an explicit tenant policy permits a
  narrower diagnostic sample.
