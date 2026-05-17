# Self-hosted Connector Bootstrap Slice

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the private-network connector promise executable at the existing runner configuration API boundary without describing Naruon as an email server.

**Architecture:** Keep GitHub self-hosted runners scoped to CI smoke checks. Expose a small bootstrap manifest from `/api/runner-config` and `/api/runner-config/rotate` so organization admins can see the intended production connector role: outbound-only control-plane connectivity to `naruon.net` and local client adapters for IMAP, POP3, SMTP, CalDAV, CardDAV, and WebDAV. The manifest must never contain the registration token or imply inbound SMTP/IMAP/MX hosting.

**Tech Stack:** FastAPI, Pydantic response models, existing organization-admin runner config API, pytest/TestClient.

---

## Source gap

- `docs/plans/2026-05-17-north-star-platform-roadmap.md` prioritizes a customer-network connector artifact instead of treating Naruon as an email server.
- `docs/operations/email-relay-proxy-boundary.md` states Naruon is a relay/proxy client over member-configured providers and explicitly forbids SMTP/IMAP server or MX-host framing.
- `backend/api/runner_config.py` already rotates organization-scoped registration tokens, but the API did not expose the connector contract or distinguish CI runner usage from production connector usage.

## Task 1: Connector manifest on runner config read

- [x] **Step 1: Write failing test**

  `backend/tests/test_runner_config_api.py` now asserts `GET /api/runner-config` returns a `connector_manifest` with:

  - `role: self-hosted_connector`
  - `network_mode: outbound_only`
  - `control_plane_domain: naruon.net`
  - local protocols: IMAP, POP3, SMTP, CalDAV, CardDAV, WebDAV
  - prohibited roles: SMTP server, IMAP server, MX host
  - runner usage: CI smoke only

- [x] **Step 2: Verify RED**

  `PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_runner_config_api.py -q` failed with `KeyError: 'connector_manifest'`.

- [x] **Step 3: Implement minimal API response contract**

  `backend/api/runner_config.py` adds a constant manifest to read responses.

## Task 2: Connector manifest on token rotation

- [x] **Step 1: Write failing test**

  `backend/tests/test_runner_config_api.py` now asserts `POST /api/runner-config/rotate` includes the same connector manifest but does not leak the `registration_token` inside that manifest.

- [x] **Step 2: Verify RED**

  The same focused pytest run failed with `KeyError: 'connector_manifest'` for rotation.

- [x] **Step 3: Implement minimal rotation response contract**

  `backend/api/runner_config.py` adds the manifest to `RunnerRotateResponse` while keeping the one-time `registration_token` only at the top level.

## Acceptance evidence

- RED: `PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_runner_config_api.py -q` failed with two expected `KeyError: 'connector_manifest'` failures before production changes.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_runner_config_api.py -q` passed with 6 tests after adding the manifest to read and rotation responses.
- Review follow-up: CodeRabbit flagged the hard-coded control-plane domain. `Settings.CONTROL_PLANE_DOMAIN` now defaults to `naruon.net`, and `test_runner_config_uses_configured_control_plane_domain` proves the manifest reflects runtime configuration.
- Full relevant backend runner config contract preserves organization-admin access control and token fingerprint behavior.
