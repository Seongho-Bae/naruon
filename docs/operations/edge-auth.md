# 인증/게이트웨이 운영 검토

Naruon의 현재 인증은 로컬 개발용 단일 mailbox bearer token 경계다. 운영 릴리스에서
다중 사용자와 외부 공개 접점을 열기 전에는 OIDC 기반 인증 관리 솔루션과 edge
gateway를 분리해서 검증해야 한다. `X-User-Id` 같은 호출자 제어 헤더는 인증으로
신뢰하지 않는다.

## 후보

- Keycloak: 표준 OIDC/SAML, realm/client/role 모델, 운영 레퍼런스가 풍부하다.
- Casdoor: 가벼운 self-hosted SSO와 OAuth/OIDC 연동에 적합하다.
- Traefik: ingress, TLS, middleware, forward-auth, rate limit을 edge에서 처리할 수
  있다.

## 권장 방향

1. Keycloak 또는 Casdoor 중 하나를 OIDC provider로 선택한다.
2. Traefik은 TLS termination, host routing, rate limit, security headers를 담당한다.
3. API는 gateway가 전달한 검증된 user/tenant claim만 신뢰한다.
4. `auth_request` 또는 forward-auth 계층은 API code와 분리해 교체 가능하게 둔다.
5. mailbox ownership migration 전에는 email/search API를 multi-tenant production으로
   열지 않는다.

## 릴리스 전 게이트

- OIDC discovery URL, JWKS rotation, client secret 저장 위치를 문서화한다.
- callback URL, logout URL, CORS origin을 환경별로 분리한다.
- tenant claim이 모든 email/search/write query에 적용되는지 integration test로 증명한다.
- Traefik middleware가 `X-Forwarded-*`, HSTS, `X-Content-Type-Options`, rate limit을
  적용하는지 smoke로 확인한다.
- Keycloak/Casdoor/Traefik 도입은 이번 `0.1.0`의 blocker가 아니라 follow-up issue로
  남긴다. 현재 릴리스는 로컬/개발 운영 경계와 live evidence stack을 먼저 고정한다.
