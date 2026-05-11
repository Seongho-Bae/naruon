# Infrastructure Evaluations and Implementation Plan

## Overview
Address remaining North Star objectives focusing on Self-hosted Runners, Database Replication, Authentication / API Gateway, and OIDC Integration.

## Target Issues
- #136: IMAP/SMTP relay-proxy self-hosted runner path design
- #137: PostgreSQL physical replication and WAL backup path design
- #138: Keycloak/Casdoor authentication, key management, and Traefik edge proxy evaluation

## Stepwise Tasks

### Task 1: Self-hosted Runner Design (Relay Proxy)
1. Add to `docs/operations/email-relay-proxy-boundary.md` the exact architecture for a self-hosted runner inside a private network, and how it executes `mail-smoke.yml`.
2. Ensure no Naruon internal code claims to *be* an email server (MX), but rather a secure conduit.

### Task 2: PostgreSQL Physical Replication & WAL Backup
1. Update `docker-compose.yml` (or create `docker-compose.postgres-ha.yml`) to include a primary and a physical replica for PostgreSQL (pgvector).
2. Configure `WAL_LEVEL=replica` on the primary and setup a read-replica container to demonstrate streaming replication.
3. Update `docs/operations/postgresql-physical-replication.md` with the new configuration.

### Task 3: Keycloak / Casdoor and Traefik Evaluation
1. Update `docker-compose.yml` to replace the Nginx proxy with Traefik (or create `docker-compose.gateway.yml`).
2. Add a Keycloak or Casdoor container to the stack.
3. Update `backend/api/auth.py` documentation / code comments to clearly map out how Traefik ForwardAuth or standard JWT bearer validation with Keycloak will replace `X-User-Id`.
4. Update `docs/operations/traefik-evaluation.md` and `docs/operations/auth-key-management.md` to confirm the decisions.

### Task 4: Verification & Integration
1. Run `docker-compose -f docker-compose.postgres-ha.yml up -d` (if applicable) and verify replication state.
2. Run `docker-compose -f docker-compose.gateway.yml up -d` to verify Traefik routing.
3. Commit and raise PR for approval.
