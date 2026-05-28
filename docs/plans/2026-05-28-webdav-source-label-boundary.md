# WebDAV Source Label Boundary Slice

## Verified Gap

- The Data and Settings workspaces are now API-wired, but WebDAV readiness and
  writeback-intent responses still expose raw `server_url` and `username` values
  to browser surfaces.
- `frontend/branding` frames Data as an operational workspace, not a credential
  inspection page. The UI needs enough source evidence for user choice while
  keeping customer provider metadata minimized.
- Existing WebDAV contracts already use opaque `source_id`; the browser does not
  need raw provider URLs or usernames to request intent-only writeback.

## Implementation Scope

- Keep `source_id`, `writeback_enabled`, and a non-sensitive `display_label` in
  `/api/webdav/accounts`.
- Keep writeback and self-sent knowledge materialization intent responses
  intent-only: `source_id`, `target_label`, `target_path`, `requires_if_match`,
  provenance, and `provider_write_executed=false`.
- Remove browser rendering and frontend mocks for WebDAV `server_url` and raw
  `username`.
- Keep actual WebDAV provider URLs and usernames server-side for future
  connector execution.

## Verification

- Backend tests prove WebDAV account and intent responses omit `server_url` and
  `username`.
- Frontend unit tests prove Data/Tasks use source-safe labels and do not render
  raw provider URLs.
- Existing signed-session/no-public-identity-header tests remain in force.
