# Self-hosted Runner Local Adapter Contract

## Goal

Remove fake IMAP/SMTP success from the customer-network connector path while
keeping Naruon framed as a web workspace/control plane, not an email server.

## Verified Gap

- `docs/operations/email-relay-proxy-boundary.md` says private-network mail
  access must go through an outbound-only customer-hosted connector.
- `backend/runner/connector.py` previously returned `IMAP data placeholder` and
  `mock_id_123` as successful `fetch_imap` and `send_smtp` responses.
- That made the runner look as if it had executed provider operations even when
  no local IMAP/SMTP adapter existed.

## Implemented Slice

- `SelfHostedConnector` now accepts optional local `imap_fetch_handler` and
  `smtp_send_handler` adapters.
- `fetch_imap` and `send_smtp` responses use a standard envelope:
  `status`, `action`, `protocol`, `account`, `request_id`, and
  `provider_write_executed`.
- If the local adapter is missing, the connector fails closed with
  `adapter_not_configured` and `provider_write_executed=false`.
- If the adapter is present, the connector forwards only the adapter's actual
  result fields inside the envelope. It does not synthesize message ids or IMAP
  data.

## Out Of Scope

- Full local IMAP/SMTP protocol implementation.
- Persisted command queues and retry scheduling.
- Provider write execution for CalDAV/CardDAV/WebDAV.

## Verification

```bash
PYTHONWARNINGS=error python3 -m pytest -q backend/tests/test_runner_connector.py
```
