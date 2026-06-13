import { NextRequest, NextResponse } from "next/server";

import {
  ANONYMOUS_SESSION_CLAIMS,
  SESSION_COOKIE_NAME,
  buildExpiredSessionCookieOptions,
  buildSessionCookieOptions,
  decodeSessionClaimsFromToken,
  normalizeSessionToken,
  sessionCookieMaxAge,
} from "@/lib/session-cookie";

export const runtime = "nodejs";

function sessionJson(token: string | null) {
  if (!token) {
    return {
      authenticated: false,
      claims: ANONYMOUS_SESSION_CLAIMS,
    };
  }
  return {
    authenticated: true,
    claims: decodeSessionClaimsFromToken(token),
  };
}

export async function GET(request: NextRequest) {
  const token = normalizeSessionToken(request.cookies.get(SESSION_COOKIE_NAME)?.value);
  return NextResponse.json(sessionJson(token));
}

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error_code: "invalid_session_request" },
      { status: 400 },
    );
  }

  const accessToken = normalizeSessionToken(
    body && typeof body === "object"
      ? (body as { access_token?: unknown }).access_token
      : null,
  );
  if (!accessToken) {
    return NextResponse.json(
      { error_code: "invalid_session_token" },
      { status: 400 },
    );
  }
  if (sessionCookieMaxAge(accessToken) === 0) {
    return NextResponse.json(
      { error_code: "expired_session_token" },
      { status: 401 },
    );
  }

  const response = NextResponse.json(sessionJson(accessToken));
  response.cookies.set(buildSessionCookieOptions(request, accessToken));
  return response;
}

export async function DELETE(request: NextRequest) {
  const response = NextResponse.json(sessionJson(null));
  response.cookies.set(buildExpiredSessionCookieOptions(request));
  return response;
}
