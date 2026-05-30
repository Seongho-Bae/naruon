# 2026-05-29 Accounts Mailbox Owner Auth Boundary

## Verified gap

- Protected-branch Strix run `26613803845` reported a critical function-level
  authorization issue on `GET /api/accounts/config`.
- The reproduced pattern was a signed JWT with `role=system_admin` and no
  organization scope being accepted by a user-owned mailbox/provider credential
  endpoint.
- This endpoint configures customer-owned SMTP, IMAP, POP3, and OAuth account
  settings. Naruon may relay or proxy against customer-designated providers, but
  it must not act as the customer's mailbox host, and operator roles must not be
  treated as the mailbox owner.

## Implemented slice

- Keep `/api/accounts/config` on the default signed-session dependency.
- Reject `system_admin` and `platform_admin` sessions before reading or writing
  mailbox/provider settings.
- Preserve scoped member and tenant sessions so normal customer account
  configuration still works.
- Add real signed bearer tests that cover the forged privileged JWT pattern and
  the preserved scoped member path.
- Record the review anti-pattern in `AGENTS.md`: elevated operators require
  separate audited support flows, not implicit access to user-owned credential
  APIs.

## Verification

- Targeted backend tests must cover `GET` and `PUT` denial before database
  lookup for privileged operator sessions.
- Existing account configuration tests must continue to cover organization
  scoping and SMTP/IMAP/POP3 validation.
- Security scanner reruns should confirm the Strix finding is gone for the PR
  head before merge.

## Remaining roadmap

- Decide and implement the explicit B2C/SOHO signed-session model before
  allowing orgless non-operator member tokens; the current shared auth layer
  still rejects those sessions.
- Design a separately audited support/impersonation flow only if product policy
  requires operator-assisted mailbox troubleshooting.
- Continue the next workspace phase after this gate fix: capture browser
  screenshots for Security/Data responsive evidence and implement the next
  source-backed operational surface gap found in `docs/plans` and
  `frontend/branding`.
