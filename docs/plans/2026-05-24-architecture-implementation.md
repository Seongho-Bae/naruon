# Architecture & API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lay the groundwork for the Self-hosted IMAP/SMTP Relay Proxy, Casdoor/Keycloak Auth Gateway (Traefik), and CalDAV/WebDAV integration.

**Architecture:** Naruon is a relay/proxy web client. Establish outbound-only WebSocket/mTLS connectors, a universal RBAC middleware, and sync APIs.

**Tech Stack:** Node.js / Python (depending on backend choice), Traefik, Keycloak/Casdoor concepts, PostgreSQL.

---

### Task 1: Self-hosted Connector & Gateway Schema

**Files:**
- Create: `backend/schema/connector.py`
- Create: `backend/api/auth.py`

- [ ] **Step 1: Define Self-hosted Connector registration schema**
- [ ] **Step 2: Define Traefik/Casdoor OIDC verification middleware**
- [ ] **Step 3: Implement unit tests for auth middleware**

### Task 2: Universal RBAC / ABAC Structure

**Files:**
- Modify: `backend/models/user.py`
- Modify: `backend/models/role.py`

- [ ] **Step 1: Define B2B2C, Admin, and B2C roles**
- [ ] **Step 2: Implement authorization dependency decorators**
- [ ] **Step 3: Add tests for hierarchical access control**

### Task 3: CalDAV/WebDAV Write-back Hooks

**Files:**
- Create: `backend/api/dav_sync.py`

- [x] **Step 1: Add `/api/calendar/writeback-intent` with provenance**
- [x] **Step 2: Support ETag / If-Match collision checks**
- [x] **Step 3: Write DAG/Ontology placeholder processing**
