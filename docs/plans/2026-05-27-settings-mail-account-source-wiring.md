# Settings Mail Account Source Wiring

## Goal

Close the Settings gap where the `연결 계정` tab still showed static provider
examples even though `/api/accounts/config` already exposes signed-session
SMTP, IMAP, POP3, and OAuth configuration with masked secrets.

## Implementation Slice

- Replace static Google/iCloud cards with source-backed protocol status cards.
- Load `/api/accounts/config` through the shared browser `apiClient` so the
  stored `naruon_session_token` is sent as `Authorization: Bearer`.
- Keep public identity headers such as `X-User-Id`, `X-Organization-Id`, and
  dev-token variants out of frontend mocks and requests.
- Render SMTP, IMAP, POP3, and OAuth fields in one responsive form.
- Preserve existing credential secrets when replacement fields are blank; do not
  replay masked secret placeholders to the backend.
- Keep copy explicit that Naruon is a web client/relay proxy, not an email
  server, mailbox-capacity provider, IMAP server, SMTP server, or MX host.

## Research Notes

- Google OAuth web-server guidance requires a client id, client secret, and
  redirect URI, and recommends keeping auth endpoints from exposing
  authorization codes to unrelated page resources:
  https://developers.google.com/identity/protocols/oauth2/web-server
- Microsoft identity platform recommends authorization code flow with PKCE for
  supported app types, and states client secrets belong to confidential web apps
  that can store them server-side:
  https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow
- RFC 7628 defines SASL OAuth mechanisms with IMAP and SMTP examples, so OAuth
  account setup must remain a provider/client adapter concern rather than a
  Naruon-hosted mailbox role:
  https://datatracker.ietf.org/doc/html/rfc7628
- RFC 8314 makes cleartext submission/access obsolete and establishes TLS as
  the baseline for email submission and access protocols:
  https://www.rfc-editor.org/rfc/rfc8314

## Verification Targets

- Frontend unit test covers account config load, signed-session headers, save
  payload shape, and no secret replay.
- Browser screenshots cover desktop, tablet, and mobile Settings scroll with the
  connected account form visible.
- Existing backend account tests remain the contract for server-side host/port
  validation and masked secret response fields.

## Deferred Connector Work

- Actual provider connection tests and provider writes remain self-hosted
  connector execution work.
- OAuth provider-specific consent flows remain an auth/connector slice after the
  generic account configuration contract is source-backed in the UI.
