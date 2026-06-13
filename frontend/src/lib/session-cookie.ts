import type { NextRequest } from "next/server";

export interface SessionClaims {
  userId: string | null;
  organizationId: string | null;
  workspaceId: string | null;
}

export const SESSION_COOKIE_NAME = "naruon_session";
export const ANONYMOUS_SESSION_CLAIMS: SessionClaims = {
  userId: null,
  organizationId: null,
  workspaceId: null,
};

const MAX_SESSION_TOKEN_LENGTH = 4096;
const CONTROL_CHARACTER_PATTERN = /[\u0000-\u001f\u007f]/;

export function normalizeSessionToken(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const token = value.trim();
  if (!token) return null;
  if (token.length > MAX_SESSION_TOKEN_LENGTH) return null;
  if (CONTROL_CHARACTER_PATTERN.test(token)) return null;
  return token;
}

export function buildSessionCookieOptions(request: NextRequest, token: string) {
  void request;
  return {
    name: SESSION_COOKIE_NAME,
    value: token,
    httpOnly: true,
    secure: true,
    sameSite: "lax" as const,
    path: "/",
  };
}

export function buildExpiredSessionCookieOptions(request: NextRequest) {
  void request;
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
