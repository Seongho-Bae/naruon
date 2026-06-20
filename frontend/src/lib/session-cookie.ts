export interface SessionClaims {
  userId: string | null;
  organizationId: string | null;
  workspaceId: string | null;
}

export const SESSION_COOKIE_NAME = "naruon_session";
export const SESSION_COOKIE_MAX_AGE_SECONDS = 12 * 60 * 60;
export const ANONYMOUS_SESSION_CLAIMS: SessionClaims = {
  userId: null,
  organizationId: null,
  workspaceId: null,
};

const MAX_SESSION_TOKEN_LENGTH = 4096;
const CONTROL_CHARACTER_PATTERN = /[\u0000-\u001f\u007f]/;
const COMPACT_JWT_PATTERN = /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/;

export function normalizeSessionToken(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const token = value.trim();
  if (!token) return null;
  if (CONTROL_CHARACTER_PATTERN.test(token)) return null;
  if (!COMPACT_JWT_PATTERN.test(token)) return null;
  return token;
}

export function buildSessionCookieOptions(token: string) {
  return {
    name: SESSION_COOKIE_NAME,
    value: token,
    httpOnly: true,
    secure: true,
    sameSite: "lax" as const,
    path: "/",
    maxAge: SESSION_COOKIE_MAX_AGE_SECONDS,
  };
}

export function buildExpiredSessionCookieOptions() {
  return {
    name: SESSION_COOKIE_NAME,
    value: "",
    httpOnly: true,
    secure: true,
    sameSite: "lax" as const,
    path: "/",
    maxAge: 0,
  };
}
