# Today Pending Replies Dashboard

Date: 2026-05-27

## Scope

Wire the Today dashboard to the existing source-backed sent-mail reply tracking
API. This slice does not add database objects and does not execute provider
writes; it surfaces the server-authoritative pending reply lane already exposed
by `/api/emails/pending-replies`.

## Confirmed Inputs

- `docs/plans/2026-05-27-sent-mail-reply-tracking-route.md` made
  `/mail?folder=sent` source-backed.
- `backend/api/emails.py` exposes `GET /api/emails/pending-replies` with
  `get_auth_context`, owner/organization scope, configured SMTP/IMAP address
  detection, self-sent exclusion, and later external-reply exclusion.
- `frontend/branding` and the GNB plan require Home to show judgment points,
  pending work, calendar conflicts, and recent mail instead of inert copy.
- The gap before this slice was frontend-only: the Today dashboard read
  `/api/emails` and `/api/tasks`, but did not read pending replies.

## Implementation Plan

1. Add pending reply loading to `WorkspaceHome` through
   `/api/emails/pending-replies?limit=3` using the shared `apiClient`.
2. Surface the count in Home KPI cards and the first summary lane.
3. Replace static judgment-point filler with the source-backed pending reply
   list, preserving safe React text rendering.
4. Add focused JSDOM coverage proving the signed `Authorization: Bearer`
   session header is used and public identity headers are not emitted.
5. Add Playwright coverage for desktop and mobile screenshots, horizontal
   overflow, and mobile dashboard scrolling.

## Verification Targets

- `npx vitest run src/components/WorkspaceHome.dashboard.test.tsx`
- `npm run lint -- src/components/WorkspaceHome.tsx src/components/WorkspaceHome.dashboard.test.tsx tests/e2e/dashboard-branding.spec.ts tests/e2e/helpers.ts`
- `npm run test:e2e -- tests/e2e/dashboard-branding.spec.ts -g "pending reply lane" --project=desktop`

## Deferred Work

- Durable reminder scheduling and notification policy for pending replies.
- Provider-side sent-folder sync completeness for all IMAP/SMTP/OAuth adapters.
- Task-board escalation when pending replies exceed workspace SLA policy.
