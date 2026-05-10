# 사내망 메일 Smoke용 self-hosted runner 설계

Naruon은 이메일 서버가 아닙니다. 자체 SMTP, IMAP, MX, 스팸 필터, 메일 릴레이를
제공하지 않는다. Naruon Client 서버는 사용자가 설정한 외부 SMTP/IMAP 서버와
통신하는 웹 클라이언트 서버다.

## 왜 self-hosted runner가 필요한가

일부 기업 환경에서는 SMTP/IMAP 서버가 사내 공개망 또는 VPN 내부에서만 접근된다.
GitHub-hosted runner는 그 네트워크에 들어갈 수 없으므로 메일 연결 smoke test만
전용 self-hosted runner에서 실행한다.

## Runner group

```text
Group: naruon-mail-smoke
Labels: self-hosted, linux, x64, mail-egress
Allowed repositories: Seongho-Bae/ai_email_client only
Network: outbound to GitHub and allowlisted SMTP/IMAP hosts only
```

## Secret

- `MAIL_SMOKE_IMAP_HOST`
- `MAIL_SMOKE_IMAP_PORT`
- `MAIL_SMOKE_SMTP_HOST`
- `MAIL_SMOKE_SMTP_PORT`
- `MAIL_SMOKE_ALLOWED_HOSTS`: 쉼표로 구분한 허용 대상. 정확한 호스트명,
  IP, CIDR를 허용한다. 비어 있으면 smoke workflow는 DNS 조회나 연결 전에
  실패한다.

사용자명과 토큰을 추가하는 인증 테스트는 별도 보호 환경에서만 켠다. PR 코드가
메일 자격 증명에 접근하면 안 되므로 `mail-smoke.yml`은 `pull_request`에서 실행하지
않는다.

## 금지 사항

- Naruon 서버에 inbound SMTP 수신 포트를 열지 않는다.
- 외부 SMTP를 대신 받아주는 relay를 만들지 않는다.
- fork PR 또는 검증되지 않은 PR 코드에 사내망 runner와 mail secret을 노출하지 않는다.

## 수동 실행

```bash
gh workflow run mail-smoke.yml
gh run watch --exit-status
```

실패 시 버그 리포트에는 provider, host, port, timeout/auth/TLS 구분, runner label,
workflow run URL을 한국어로 적는다. secret 값은 적지 않는다.
