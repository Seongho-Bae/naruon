submit \
--title "🔒 테스트 환경의 하드코딩된 세션 토큰 패턴 수정" \
--body "🎯 **What:**
프론트엔드 테스트 코드 내에서 사용되던 \`header.payload.signature\` 형태의 하드코딩된 토큰 패턴을 \`test-header.test-payload.test-signature\`로 교체했습니다. 대상 파일은 다음과 같습니다:
- \`frontend/src/lib/session-cookie.test.ts\`
- \`frontend/src/app/auth/oidc/callback/route.test.ts\`
- \`frontend/src/lib/api-client.test.ts\`

⚠️ **Risk:**
해당 코드는 테스트 파일 내에 위치하므로 실제 운영 환경의 세션을 노출시키는 심각한 보안 취약점은 아닙니다. 하지만 실제 토큰과 유사한 형태의 문자열을 코드에 하드코딩하는 것은 좋은 보안 위생(Security Hygiene) 상태가 아니며, CodeQL, Strix, Bandit 등 보안 스캐너에서 하드코딩된 자격 증명(Hardcoded credentials) 오탐지로 분류될 가능성이 큽니다.

🛡️ **Solution:**
스캐너에서 오탐을 피하고 개발자가 테스트 목적임을 확실히 알 수 있도록 명백한 가짜 토큰(Dummy token) 형식인 \`test-header.test-payload.test-signature\`로 일괄 대체했습니다. 하이픈(\`-\`)은 base64url 형식에서 유효한 문자이므로 기존의 JWT 패턴 검증 정규식(\`COMPACT_JWT_PATTERN\`)을 그대로 통과하여 기존 테스트의 기능(Functionality)을 깨지 않고 정상 동작합니다."
