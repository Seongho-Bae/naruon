## 2026-05-28 - Missing Default Security Headers in FastAPI
**Vulnerability:** The FastAPI application was missing standard HTTP security headers such as Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options, and Content-Security-Policy in its default responses.
**Learning:** By default, FastAPI does not automatically inject these defense-in-depth headers, leaving the application potentially more susceptible to MIME-sniffing, clickjacking, and injection downgrade paths. X-XSS-Protection is deprecated by major browsers and should not be the default XSS control.
**Prevention:** Always add a global middleware (e.g., via `@app.middleware("http")` or dedicated security middleware plugins) early in the FastAPI application setup to enforce standard security headers across all endpoints, and use a configurable Content-Security-Policy as the modern XSS and framing control.
## 2026-06-07 - Missing 'no-new-privileges' in Traefik Service
**Vulnerability:** The docker-compose.infra.yml file defined a service 'traefik' without the 'no-new-privileges' security option. This allows the service to escalate privileges via setuid or setgid binaries.
**Learning:** Found by Strix AI. Without `no-new-privileges:true`, an attacker who compromises the container could escalate to root.
**Prevention:** Always add `security_opt: - no-new-privileges:true` to Docker container configurations, especially for ingress services like Traefik.
