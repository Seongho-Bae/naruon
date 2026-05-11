# Traefik Edge Proxy and Authentication Integration

## 확인된 사실 / Confirmed

- `k8s/ingress.yaml` currently uses NGINX ingress annotations.
- `docker-compose.gateway.yml` now implements a Traefik API gateway integrated with Keycloak for API protection and routing.

## Traefik & Keycloak/Casdoor 평가 (Issue #138)

- **OIDC / SSO 보호:** 백엔드의 `/api` 경로를 Keycloak(또는 Casdoor)의 OpenID Connect 흐름 뒤로 숨길 수 있도록 Traefik ForwardAuth(또는 플러그인) 설계를 실험할 수 있는 기반이 마련되었습니다.
- **Header 전파 (Identity):** 기존 더미 `X-User-Id` 로직 대신, Traefik이 인증 후 내려주는 서명된 헤더(Authorization/JWT)를 `backend/api/auth.py`가 검증하도록 구조를 고도화할 계획입니다.
- **로컬 E2E Parity:** Nginx Proxy 대신 `docker-compose.gateway.yml`을 통해 mTLS와 ACME/Let's Encrypt 프로비저닝을 클라우드와 동일한 설정 파일(`traefik.yml` 정적/동적 설정)로 관리할 수 있습니다.

## 평가 항목

- OIDC/forward-auth integration with Keycloak and Casdoor.
- Header propagation to FastAPI without trusting client-controlled identity.
- mTLS/TLS termination and ACME storage hardening.
- Kubernetes rollout and rollback compared with current NGINX ingress.
- Local E2E parity through a metadata-only smoke path that does not execute PR
  code in privileged contexts.
