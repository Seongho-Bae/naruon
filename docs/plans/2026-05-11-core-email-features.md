# Core Email Features Implementation Plan

## Overview
Transform Naruon from a mocked skeleton into a functional email client proxy. Implement real IMAP syncing, SMTP sending, and replace the dummy auth mechanism.

## Issue Reference
- Target Issue: #146

## Constraints & Requirements
- TDD strictly followed: write failing tests first.
- Maintain existing architecture (FastAPI, SQLAlchemy, Next.js).
- Ensure Live E2E tests pass after implementation.
- All code must handle exceptions gracefully to avoid worker crashes.

## Stepwise Tasks

### Task 1: SMTP Sending Implementation
1. Remove `simulated: True` from `backend/services/email_client.py`.
2. Implement real SMTP sending logic using `aiosmtplib` (or `smtplib` run in thread).
3. Handle SMTP authentication using tenant config credentials.
4. Verify with a live test (or mocked test checking SMTP commands if external network is unavailable).

### Task 2: IMAP Sync Worker Implementation
1. Flesh out the `_sync_tenant` logic in `backend/services/imap_worker.py`.
2. Connect to the IMAP server and FETCH recent emails.
3. Parse the fetched emails (using the existing `email_parser.py`).
4. Save parsed emails to the database using SQLAlchemy.
5. Provide robust error handling to skip failing tenants without crashing the whole worker loop.

### Task 3: Real Authentication Mechanism
1. Evaluate replacing `X-User-Id` dummy auth in `backend/api/auth.py`.
2. Integrate a more robust token-based auth or tie into a proper Keycloak/Casdoor evaluation framework if available, or simply use secure JWTs.
3. Ensure the frontend correctly passes these secure tokens.

### Task 4: Verification & Integration
1. Run full `pytest` suite.
2. Run `npm test` and `npm run build` on the frontend.
3. Run Live E2E tests (`docker-compose.live-e2e.yml`).
4. Resolve any security, linter, or functional regressions.
