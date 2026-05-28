# Provider Connection Onboarding Slice

## Goal

Turn the remaining Settings connection gap into an API-wired onboarding surface
without changing Naruon into an SMTP, IMAP, CalDAV, or WebDAV host. Customer
data remains in member-selected providers; Naruon stores connection metadata,
masked secrets, source registry intent, and connector control-plane state.

## Confirmed Gaps

- `frontend/branding` and the Settings roadmap expect users to choose and
  operate connected providers from Settings, but the previous surface only
  showed SMTP/IMAP/POP3/OAuth fields.
- `TenantConfig` was unique by `user_id`, so the same person could not maintain
  separate account configuration for two organizations.
- Legacy `/api/config` and runtime consumers still queried provider settings by
  user only, which would leak or select the wrong provider row after scoped rows
  are introduced.
- Self-hosted connector token rotation existed in the backend but was not
  exposed in Settings. The manifest must keep the role outbound-only and must
  not imply SMTP/IMAP/MX hosting.
- CalDAV/CardDAV/WebDAV readiness existed in Calendar/Data surfaces but was not
  visible where provider onboarding is managed.

## Implementation Scope

- Add `tenant_configs.organization_id` and scoped uniqueness over
  `user_id + organization_id` while preserving personal rows as
  `organization_id IS NULL`.
- Route `/api/accounts/config`, legacy `/api/config`, LLM/search/email runtime
  consumers, and reply tracking through a shared scoped lookup helper.
- Make `/api/accounts/config` GET return an empty response without creating a DB
  row; only PUT creates or updates connection settings.
- Extend Settings `연결 계정` to load signed-session CalDAV/CardDAV and WebDAV
  source readiness from `/api/calendar/writeback-sources` and
  `/api/webdav/accounts`.
- Show OAuth app readiness truthfully as app-configured/consent-pending; actual
  provider-specific token exchange remains a future connector/auth slice.
- Expose `/api/runner-config/rotate` in Settings for organization admins as a
  one-time token action, keeping the token outside the connector manifest.

## Non-Goals

- No provider write execution in the browser.
- No Naruon-hosted mailbox, SMTP server, IMAP server, MX host, CalDAV host, or
  WebDAV storage capacity.
- No provider-specific OAuth authorization-code exchange in this slice.

## Verification

- Backend tests must prove same `user_id` can hold different provider settings
  per organization and that legacy `/api/config` is not a user-only bypass.
- Frontend unit tests must prove signed-session bearer usage for account config,
  CalDAV/WebDAV readiness, and runner token rotation, with no public identity
  headers.
- Responsive browser evidence must cover desktop, tablet, and mobile Settings
  connection screens, including scroll and mobile navigation sanity.
