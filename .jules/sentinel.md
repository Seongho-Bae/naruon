## 2026-06-26 - Information Disclosure via X-Powered-By Header
**Vulnerability:** Next.js exposes the 'X-Powered-By: Next.js' HTTP header by default, which discloses the technology stack being used to potential attackers.
**Learning:** The default configuration in `next.config.ts` did not explicitly disable this header using the `poweredByHeader` option.
**Prevention:** Always explicitly set `poweredByHeader: false` in `next.config.ts` to minimize the attack surface and prevent unnecessary information leakage.
