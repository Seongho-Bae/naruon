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
const BASE64URL_SEGMENT_PATTERN = /^[A-Za-z0-9_-]+$/;

export function normalizeSessionToken(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const token = value.trim();
  if (!token) return null;
  if (token.length > MAX_SESSION_TOKEN_LENGTH) return null;
  if (CONTROL_CHARACTER_PATTERN.test(token)) return null;
  return token;
}

function decodeBase64UrlJson(segment: string): unknown {
  if (!BASE64URL_SEGMENT_PATTERN.test(segment)) return null;
  const normalized = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
  const json =
    typeof Buffer !== "undefined"
      ? Buffer.from(padded, "base64").toString("utf8")
      : atob(padded);
  return JSON.parse(json);
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const [, payloadSegment] = token.split(".");
  if (!payloadSegment) return null;

  try {
    const payload = decodeBase64UrlJson(payloadSegment);
    return payload && typeof payload === "object"
      ? (payload as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

function stringClaim(payload: Record<string, unknown>, name: string) {
  const value = payload[name];
  return typeof value === "string" ? value.trim() || null : null;
}

export function decodeSessionClaimsFromToken(token: string): SessionClaims {
  const payload = decodeJwtPayload(token);
  if (!payload) return ANONYMOUS_SESSION_CLAIMS;
  return {
    userId: stringClaim(payload, "sub"),
    organizationId: stringClaim(payload, "org"),
    workspaceId: stringClaim(payload, "workspace"),
  };
}

export function sessionCookieMaxAge(token: string, now = Date.now()) {
  const payload = decodeJwtPayload(token);
  const exp = payload?.exp;
  if (typeof exp !== "number" || !Number.isFinite(exp)) return undefined;

  const remainingSeconds = Math.floor(exp - now / 1000);
  return remainingSeconds > 0 ? remainingSeconds : 0;
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
    maxAge: sessionCookieMaxAge(token),
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
