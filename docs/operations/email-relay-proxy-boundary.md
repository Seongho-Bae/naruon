# Email Relay/Proxy Boundary

## 확인된 사실 / Confirmed

- Naruon is not an email server. It is a web client server that can relay/proxy
  member-configured SMTP/IMAP providers.
- `backend/api/emails.py` sends through `services.email_client.send_email` only
  when a tenant SMTP configuration exists; missing SMTP config returns a 400.
- `backend/services/imap_worker.py` connects to configured IMAP endpoints as a
  client; it does not listen for inbound mail or own MX records.
- `backend/api/auth.py` still uses dummy `X-User-Id` auth, so mailbox ownership
  and production tenancy are not complete.

## 가설 / Hypothesis

- 사내망 SMTP/IMAP smoke는 `mail-egress` self-hosted runner와 environment secrets
  로만 실행해야 하며 fork PR 또는 untrusted workflow가 내부 endpoint를 만지면 안 됩니다.
- A future relay/proxy path should validate allowed hosts, ports, TLS mode, and
  tenant ownership before opening network connections.

## 금지 사항

- Do not describe Naruon as an SMTP server, IMAP server, MX host, or mail transfer
  authority.
- Do not add inbound listener ports or public MX assumptions without a separate
  architecture decision and security review.
