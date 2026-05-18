# Naruon North Star Platform Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the product roadmap with Naruon's north star: an AI workspace that connects external email, calendar, files, prompts, and enterprise policy without becoming an email host.

**Architecture:** Use a self-hosted connector for private-network protocols, a SaaS control plane for workspace/auth/policy/AI, and explicit data-sovereignty writeback to customer-owned mail, CalDAV, and WebDAV accounts. Implement in thin, testable slices: first make visible menus truthful, then add mailbox-scoped auth/ownership, then connector/writeback domains.

**Tech Stack:** Next.js 16, FastAPI, PostgreSQL, GitHub Actions, self-hosted runners/connectors, Keycloak-first OIDC option, Traefik gateway option, OpenTelemetry + Prometheus/Loki/Tempo/Grafana, IMAP/POP3/SMTP, CalDAV/CardDAV/WebDAV.

---

## Confirmed facts

- `docs/operations/email-relay-proxy-boundary.md` states Naruon is not an SMTP/IMAP server or MX host; it is a web client server and relay/proxy for member-configured providers.
- `frontend/src/components/DashboardLayout.tsx` already exposes primary IA (`AI 허브`, `프롬프트`, `설정`, mobile search/calendar/actions), but several destinations remain disabled or thin.
- `backend/api/auth.py` no longer uses header-derived development identity.
  Production-grade OIDC/RBAC/ABAC and audited mailbox-owner backfill remain
  incomplete.
- `backend/db/models.py` has organization and scoped role primitives, but persisted emails are not mailbox-account scoped.
- `.github/workflows/mail-smoke.yml` uses `[self-hosted, mail-egress]` for internal mail connectivity smoke, but there is no implemented customer connector/runner artifact.
- `.github/workflows/pr-governance.yml` exists, but Strix workflow naming, blocker exit behavior, and comment dedupe need hardening.

## External research anchors

- Self-hosted runner pattern: GitHub self-hosted runners and GitLab Runner keep network-local access inside customer infrastructure.
- Protocol standards: IMAP RFC 9051, SMTP RFC 5321, CalDAV RFC 4791, CardDAV RFC 6352, service discovery RFC 6764.
- Provider APIs: Gmail API and Microsoft Graph mail are preferred when available; IMAP/SMTP/POP3 remain required for private/legacy servers.
- Auth: Keycloak is the enterprise default for realms, federation, identity brokering, and authorization services. Casdoor is lighter and Casbin-friendly when operations simplicity wins.
- Gateway/APM: Traefik is suitable for TLS/routing/ForwardAuth/rate limits. OpenTelemetry + Collector with Prometheus, Loki, Tempo/Jaeger, and Grafana is the open-source observability baseline.

## North-star architecture

```text
Customer network / private VPC
  └─ Naruon self-hosted connector
       ├─ OAuth provider API adapters
       ├─ IMAP / POP3 / SMTP client adapters
       ├─ CalDAV / CardDAV / WebDAV adapters
       ├─ ZIP / forwarded-mail import adapters
       └─ outbound-only mTLS/WebSocket/queue channel
             ↓
Naruon SaaS control plane (naruon.net)
  ├─ Traefik edge / route policy / coarse auth middleware
  ├─ OIDC IdP option: Keycloak default, Casdoor lighter alternative
  ├─ App policy service: RBAC + ABAC + delegation + sovereignty
  ├─ Workspace APIs: mail, search, prompts, AI hub, calendar/writeback intents
  ├─ Sync/indexing/AI workers with tenant/mailbox scope on every job
  └─ OpenTelemetry Collector → Prometheus + Loki + Tempo/Jaeger + Grafana
```

## Prioritized roadmap

1. **Functional IA and dead-space reduction**
   - Make `/ai-hub` a real three-section workspace: `맥락 종합`, `판단 포인트`, `실행 항목`.
   - Replace generic English/filler copy and disabled high-frequency menus with actionable empty/error states.
   - Keep startup dashboard/email/calendar choice, but make dashboard/calendar API-backed in the next slice.

2. **Mailbox ownership, auth, RBAC/ABAC**
   - Keep RED/GREEN regression tests proving list/detail/thread/search cannot
     cross mailbox ownership boundaries.
   - Introduce `MailboxAccount` and owner-scope model before broad OIDC claims are trusted.
   - Default IdP design: Keycloak for enterprise federation; Casdoor as optional lighter deployment.
   - Enforce ABAC denial precedence over RBAC allow for data region, delegation, consent, and resource ownership.

3. **Connector and relay/proxy boundary**
   - Implement customer-network connector artifact instead of describing Naruon as an email server.
   - Connector uses outbound-only control channel and local IMAP/POP3/SMTP/CalDAV/WebDAV access.
   - GitHub self-hosted runner remains CI smoke infrastructure, not the production relay itself.

4. **CalDAV/CardDAV/WebDAV data sovereignty and writeback**
   - Phase 1: read-only sync/index from N accounts.
   - Phase 2: opt-in writeback with ETag/If-Match conflict handling, provenance, audit logs, and per-source capability detection.
   - Naruon-created objects must choose the most appropriate customer-owned account/calendar/folder, not store only in Naruon.

5. **Dedupe/threading across ZIP/import/forwarding**
   - Use mailbox-scoped source keys, normalized Message-ID, content fingerprints, forwarded-chain provenance, and attachment fingerprints.
   - Same `Message-ID` in different mailbox accounts must not collide.
   - Duplicate candidates link to canonical message/thread instead of visible duplicate rows.

6. **Open-source observability**
   - Update stale APM docs and add OTel Collector/Alloy path.
   - Track connector heartbeat, sync lag, provider throttling, writeback conflicts, tenant-level latency, AI action audit trails.
   - Redact email body, subject where policy requires, secrets, DSNs, calendar/contact PII.

7. **PR automation governance**
   - Fix PR Governance workflow names, blocker exit behavior, and idempotent comments.
   - Keep privileged PR scans trusted-base/data-only, no untrusted checkout with secrets.
   - Required human approval should remain zero under repo policy; platform refusal is external blocker evidence, not a reason to wait silently.

## First implementation slice

Implement `/ai-hub` as the real branded AI workspace.

- File plan: `docs/plans/2026-05-17-ai-hub-functional-workspace.md`
- Why first: it directly reduces visible dead space and makes the primary nav promise true without introducing new backend endpoints.
- Acceptance: loading, error, empty, and success states; responsive/no-horizontal-overflow; mobile nav label consistency; unit and Playwright evidence.
