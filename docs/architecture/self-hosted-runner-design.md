# Self-Hosted Runner Architecture

## Overview
Naruon operates as a Web Client and AI Workspace, not as an email hosting server. Many enterprise and SMB customers operate their own private email servers (e.g., on-premise Microsoft Exchange, internal postfix/dovecot, or private cloud IMAP/SMTP). 
To connect to these private network mail servers without exposing them to the public internet, Naruon uses a **Self-Hosted Runner**.

## Design Principles
1. **Outbound-Only Connection**: The self-hosted runner is deployed inside the customer's private network (VPC/Intranet). It establishes an outbound-only connection (e.g., WebSockets, gRPC, or long-polling) to the Naruon Control Plane (`naruon.net`). Customers do not need to open inbound firewall ports.
2. **Local Protocol Proxy**: The runner acts as a local proxy, speaking standard protocols (IMAP, POP3, SMTP, CalDAV, WebDAV) to the internal mail and file servers.
3. **Data Sovereignty**: The runner retrieves emails and metadata, performs necessary local encryption or redaction (if configured by enterprise policy), and securely transmits it to Naruon for AI processing. For writebacks (e.g., sending an email or updating a calendar), Naruon pushes the intent to the runner, which executes it locally.

## Components

### 1. Naruon Control Plane (SaaS)
- Maintains WebSocket connections with registered runners.
- Holds the configuration for each tenant (e.g., Target Internal IP, Port).
- Manages AI capabilities, deduplication, threading, and user sessions.
- Exposes organization-admin operational state through
  `/api/observability/operational-signals`, including connector registration,
  active outbound connection count, last in-process heartbeat, and APM
  configuration. Persistent heartbeat and runner command outcome history now use
  scoped `ConnectorSignalEvent` rows. Transient writeback dispatch failures are
  persisted as encrypted `provider_writeback_retry_items`; the backend retry
  worker processes due items with idempotent state transitions and exhaustion
  handling. Organization-admin observability surfaces aggregate retry queue depth
  by state without exposing payloads, provider credentials, or retry item ids.

### 2. The Self-Hosted Runner (Customer Network)
- Distributed as a lightweight Docker container.
- Written in Python (sharing models/schemas with the main Naruon backend) or Go (for minimal footprint).
- Authenticates with Naruon using a `Registration Token` mapped to the `organization_id` and `workspace_id`.
- Periodically polls or maintains a persistent connection for tasks (e.g., "Send email", "Fetch new emails").
- Executes private-network protocol commands only through configured local
  adapters. The Python connector now provides explicit IMAP fetch/import and
  SMTP send local adapter handlers plus ETag/If-Match-guarded CalDAV/WebDAV PUT
  handlers that can be passed into `SelfHostedConnector`.
  Missing protocol adapters must still return `adapter_not_configured` with
  `provider_write_executed=false`; the runner must not create mock message ids,
  placeholder IMAP data, or other fake provider-success evidence.

## Security & RBAC/ABAC
- The runner only executes commands authorized by the Naruon RBAC/ABAC policy engine.
- Connections are secured via mTLS or HTTPS/WSS.
- All credentials (IMAP/SMTP passwords) can either be stored securely on the Naruon SaaS (encrypted via Fernet) or injected locally into the runner via environment variables, depending on customer security posture.

## Implementation Steps
1. The repository now includes a minimal `connector/` CLI/container entrypoint
   that runs `SelfHostedConnector` with the server-issued registration token and
   signed session bearer credential. Until local adapters are configured,
   commands fail closed with `adapter_not_configured`.
2. Expose WebSocket or HTTP polling endpoints on the Naruon backend.
3. Update `WorkspaceRunnerConfig` in `backend/db/models.py` to manage runner lifecycle.
4. Persist connector heartbeat, command outcome, retry queue, retry worker, and
   aggregate queue depth so the APM dashboard can move from in-process status to
   durable operational history.
