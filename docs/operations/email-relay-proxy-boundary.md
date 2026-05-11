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

## 사내망 Self-hosted Runner 아키텍처 (Issue #136)

- **배경:** 공개망에서 접근할 수 없는 사내망 내부의 IMAP/SMTP 서버와 Naruon 간의 통신 무결성을 검증하기 위해, `mail-egress` 라벨을 가진 Self-hosted runner 구조가 설계되었습니다.
- **워크플로우 검증:** `.github/workflows/mail-smoke.yml`은 오직 신뢰할 수 있는 `workflow_dispatch`나 스케줄로만 작동하며, 프라이빗 네트워크에 배치된 Runner가 내부 DNS를 통해 사내 메일 서버 연결성(Connectivity)을 검증합니다.
- **의도된 한계점:** Naruon은 그 자체로 메일을 수신하거나 SMTP로 메일을 릴레이하는 MX Host가 아니며, 어디까지나 Tenant (사용자)가 입력한 자격 증명을 바탕으로 TCP/TLS 기반의 메일 프로토콜 클라이언트(Proxy) 역할만을 수행합니다.

## 금지 사항

- Do not describe Naruon as an SMTP server, IMAP server, MX host, or mail transfer
  authority.
- Do not add inbound listener ports or public MX assumptions without a separate
  architecture decision and security review.
