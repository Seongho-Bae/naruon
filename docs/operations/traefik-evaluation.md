# Traefik Evaluation

## 확인된 사실 / Confirmed

- `k8s/ingress.yaml` currently uses NGINX ingress annotations and routes `/api`
  to backend and `/` to frontend.
- `docker-compose.live-e2e.yml` uses nginx only as a local E2E reverse proxy; it
  is not a production gateway contract.
- No Traefik manifests, middleware, forward-auth, or ACME configuration exist in
  the repository today.

## 가설 / Hypothesis

- Traefik is worth evaluating if edge OIDC/forward-auth, TLS automation, and
  service discovery reduce operational burden compared with the current NGINX
  ingress assumption.
- Traefik should not be adopted until Keycloak/Casdoor, mailbox ownership, and
  secret-management boundaries are decided.

## 평가 항목

- OIDC/forward-auth integration with Keycloak and Casdoor.
- Header propagation to FastAPI without trusting client-controlled identity.
- mTLS/TLS termination and ACME storage hardening.
- Kubernetes rollout and rollback compared with current NGINX ingress.
- Local E2E parity through a metadata-only smoke path that does not execute PR
  code in privileged contexts.
