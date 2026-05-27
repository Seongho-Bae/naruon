# Sent Mail Reply Tracking Route

Date: 2026-05-27

## Scope

Make `/mail?folder=sent` a real API-backed sent-mail lane instead of a menu-only
promise. The slice reuses existing email rows and reply-tracking fields; it does
not add database tables or provider write execution.

## Confirmed Inputs

- The workspace navigation already links to `/mail?folder=sent` as "보낸 메일".
- `backend/api/emails.py` already returns `is_self_sent` and `requires_reply`.
- `services/reply_tracking_service.py` already derives user-owned addresses from
  configured SMTP/IMAP usernames and detects self-sent notes.
- `EmailList.tsx` only called `/api/emails`, so the sent route was visually
  indistinguishable from the inbox.

## Product Research Notes

- Gmail Help documents follow-up nudges for sent emails that may need a reply:
  https://support.google.com/mail/answer/6585
- Microsoft Outlook best-practice guidance treats follow-up timing as part of
  mail workflow hygiene:
  https://support.microsoft.com/en-us/office/best-practices-for-outlook-f90e5f69-8832-4d89-95b3-bfdf76c82ef8
- Inbox Zero's Reply Zero pattern separates "awaiting reply" sent threads into a
  waiting lane:
  https://docs.getinboxzero.com/essentials/reply-zero

## Implementation Plan

1. Backend folder filter
   - Add `folder=inbox|sent` to `GET /api/emails`.
   - Keep the default inbox behavior compatible with existing grouped-thread
     results.
   - For `folder=sent`, return only threads containing a message from the
     authenticated user's configured SMTP/IMAP address.
   - Preserve owner and organization scoping.

2. Frontend route wiring
   - Parse `folder=sent` in `/mail`.
   - Pass the folder to `WorkspaceHome` and all `EmailList` instances.
   - Fetch `/api/emails?folder=sent` with the stored signed session token.

3. Sent-mail surface
   - Render "보낸 메일", "답변 추적", and "지식 정리" copy.
   - Keep existing `응답 대기 중` and `지식 정리` badges from API fields.
   - Preserve safe text rendering for sender, subject, and snippet.

4. Verification
   - Backend tests for sent filtering and invalid folder rejection.
   - Frontend tests for sent mode endpoint and labels.
   - E2E screenshots for desktop and mobile including scroll.

