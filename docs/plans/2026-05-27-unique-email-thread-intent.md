# Unique Email Canonical Thread Intent Slice

> **For agentic workers:** Use subagent-driven review plus stepwise PR
> governance. Keep this slice intent-only: no provider write, no irreversible DB
> merge, and no subject-only automatic thread merge.

**Goal:** Turn the Data workspace duplicate-import requirement into a signed API
intent that can evaluate ZIP-imported and forwarded duplicate emails against the
current user's canonical threads.

**Architecture:** Naruon remains a web client/control plane. Customer mail
servers stay the source of truth. This slice reads existing owner-scoped `emails`
rows and returns server-authoritative intent metadata only. It does not create a
mail server, write to a provider, or persist duplicate provenance yet.

## Confirmed gap

- `docs/plans/2026-05-19-branding-menu-task-tracking-gap-closure.md` keeps
  duplicate ZIP/forward import handling as remaining north-star work.
- `frontend/src/components/DataLayout.tsx` described duplicate thread cleanup but
  had no API-wired action.
- `backend/services/threading_service.py` had a subject fallback for `Fwd:` and
  `Re:` imports. That can merge unrelated conversations and is not a strong
  duplicate signal.

## Implemented slice

- `POST /api/emails/unique-thread-intent`
  - signed-session private route through the existing email router
  - accepts up to 20 import candidates
  - checks owner/org-scoped existing email rows by normalized Message-ID and
    strong body fingerprint
  - returns canonical thread ids, match reason, provenance, and audit event
  - returns `provider_write_executed: false`
- Data workspace action
  - calls the signed API through `apiClient`
  - strips public identity headers
  - renders candidate count, duplicate count, audit event, provider-write flag,
    and per-candidate canonical thread mapping
- Threading hardening
  - subject-only forwarded/reply fallback removed from `assign_thread_id`
  - future forwarded threading must come from Message-ID, References,
    In-Reply-To, or explicit duplicate provenance
- IMAP import hardening
  - newly fetched emails now store the same strong body fingerprint when body
    content is available, with the prior lightweight fingerprint kept only as a
    fallback

## Out of scope

- Persisted duplicate provenance table such as `email_import_events`.
- ZIP importer rewiring and persisted duplicate provenance for source account
  history.
- Attachment hashing and forwarded-body original header extraction.
- Provider writes or customer mail server mutation.

## Verification targets

```bash
python3 -m pytest backend/tests/test_emails_api.py -k 'unique_email_thread_intent' -q
python3 -m pytest backend/tests/test_threading_service.py -q
cd frontend && npm test -- --run src/app/data/page.test.tsx
```

Browser evidence must include `/data` desktop and mobile screenshots after
creating the unique thread intent, plus mobile scroll proof that bottom content
is reachable above the fixed navigation.
