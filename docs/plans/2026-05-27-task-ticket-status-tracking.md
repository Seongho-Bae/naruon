# Source-Linked Ticket Status Tracking Slice

<!-- markdownlint-disable MD013 -->

## Goal

Move Naruon task management beyond passive todos by letting users update the
status of source-linked ticket tasks through the signed API. The task remains
linked to the originating email/thread and continues to expose only the opaque
`task_uid` as the public `id`.

## Product Research Notes

- Atlassian describes ticket workflows as status plus transitions; status shows
  where a work item is in the workflow, and transition is the action that moves
  it between statuses:
  <https://www.atlassian.com/software/jira/guides/workflows/overview>
- Jira's default work item model keeps status and priority as first-class
  reporting fields:
  <https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-statuses-priorities-and-resolutions/>
- Jira board columns map statuses to visible workflow lanes, with simple default
  columns such as To Do, In Progress, and Done:
  <https://support.atlassian.com/jira-software-cloud/docs/configure-columns/>

## Implementation

- Add `PATCH /api/tasks/{task_uid}` with signed-session auth and tenant owner
  scope. The endpoint accepts `status` and/or `priority`, rejects empty payloads,
  returns 404 for tasks outside the authenticated tenant, and never exposes
  sequential database ids.
- Add `apiClient.patch` so browser writes keep the HttpOnly cookie-backed proxy
  session and continue stripping browser `Authorization` plus public identity
  headers.
- Update `/tasks` so actual API ticket cards expose status transition buttons
  for `open`, `in_progress`, `blocked`, and `done`; counts update from the
  server response.
- Keep the existing mock kanban demonstration for now, but make the route header
  responsive so mobile screenshots do not overflow while the live ticket queue
  is being operated.

## Verification

```bash
python3 -m pytest backend/tests/test_tasks_api.py -q
npm test -- src/app/tasks/page.test.tsx
npm run lint
npm run typecheck
npm run build
PLAYWRIGHT_PORT=18170 LIVE_BASE_URL=http://127.0.0.1:18170 npx playwright test tests/e2e/dashboard-branding.spec.ts --project=desktop -g "task ticket status"
```

The Playwright run must capture desktop, mobile, and mobile-scroll screenshots
and verify the PATCH request uses the signed session without public identity
headers.
