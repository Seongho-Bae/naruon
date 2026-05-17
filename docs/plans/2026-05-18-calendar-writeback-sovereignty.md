# Calendar Writeback Sovereignty Slice

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make calendar writeback choose customer-owned CalDAV/CardDAV/WebDAV sources instead of treating Naruon as the system of record.

**Architecture:** Add a thin `/api/calendar/writeback-intent` API that accepts available source capabilities, selects an owned write-enabled external source, and returns an intent with provenance, audit event name, and ETag/If-Match requirements for updates. This is an intent contract only: it does not write to provider APIs yet, and it does not store created objects only inside Naruon.

**Tech Stack:** FastAPI, Pydantic input validation, existing dev-header auth context, pytest/TestClient.

---

## Source gap

- `docs/plans/2026-05-17-north-star-platform-roadmap.md` requires explicit data-sovereignty writeback to customer-owned mail, CalDAV, and WebDAV accounts.
- Phase 2 writeback must use ETag/If-Match conflict handling, provenance, audit logs, and per-source capability detection.
- Existing `POST /api/calendar/sync` writes directly to Google Calendar from a supplied token and does not describe source selection, ownership, or sovereignty semantics.

## API security scope

- Surface changed: authenticated private HTTP endpoint `POST /api/calendar/writeback-intent`.
- AuthN/AuthZ gate: uses `get_auth_context`; selected source owner must match the current user.
- Input validation: Pydantic constrains action and source protocol values.
- Secret/PII output: response does not echo user tokens or provider credentials; it returns only source id, protocol, provenance, and audit metadata.
- Abuse/rate limiting: no provider write happens in this slice, so endpoint cost is bounded to request validation and source selection.

## Task 1: Select customer-owned writeback source

- [x] **Step 1: Write failing test**

  `backend/tests/test_calendar_api.py` now requires `/api/calendar/writeback-intent` to skip the Naruon cache source and choose a write-enabled CalDAV account owned by the current user.

- [x] **Step 2: Verify RED**

  Focused pytest failed with 404 because the endpoint did not exist.

- [x] **Step 3: Implement minimal endpoint**

  `backend/api/calendar.py` adds Pydantic request/response models and returns a customer-owned writeback intent.

## Task 2: Preserve ETag conflict contract for updates

- [x] **Step 1: Write failing test**

  The update test requires `requires_if_match: true` and `if_match` set to the selected source ETag.

- [x] **Step 2: Implement minimal ETag gate**

  Updates now require an ETag and return it as the If-Match value.

## Task 3: Reject non-owner and Naruon-only storage

- [x] **Step 1: Write failing test**

  The rejection test requires 403 for a source owned by another user and 422 when only local/Naruon storage is available.

- [x] **Step 2: Implement minimal authorization and sovereignty checks**

  The endpoint rejects cross-owner source selection and refuses local-only writeback candidates.

## Acceptance evidence

- RED: `PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_calendar_api.py -q` failed with three expected 404s before endpoint implementation.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_calendar_api.py -q` passed with 5 tests after endpoint implementation.
