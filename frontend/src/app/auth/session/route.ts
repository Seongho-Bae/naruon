import { NextRequest, NextResponse } from "next/server";

import {
  ANONYMOUS_SESSION_CLAIMS,
  SESSION_COOKIE_NAME,
  buildExpiredSessionCookieOptions,
  buildSessionCookieOptions,
  normalizeSessionToken,
  type SessionClaims,
} from "@/lib/session-cookie";
import { backendApiBaseUrl } from "@/lib/backend-url";

export const runtime = "nodejs";

type BackendSessionResponse = {
  user_id?: unknown;
  organization_id?: unknown;
  workspace_id?: unknown;
};

function stringClaim(value: unknown) {
  return typeof value === "string" ? value.trim() || null : null;
}

function claimsFromBackendSession(body: BackendSessionResponse): SessionClaims | null {
  const userId = stringClaim(body.user_id);
  const workspaceId = stringClaim(body.workspace_id);
  if (!userId || !workspaceId) return null;
  return {
    userId,
    organizationId: stringClaim(body.organization_id),
    workspaceId,
  };
}

async function verifySessionToken(token: string): Promise<SessionClaims | null> {
  const target = backendApiBaseUrl();
  target.pathname = "/api/auth/session";
  target.search = "";

  try {
    const response = await fetch(target, {
      method: "GET",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });
    if (!response.ok) return null;

    const body = (await response.json()) as BackendSessionResponse;
    return claimsFromBackendSession(body);
  } catch {
    return null;
  }
}

function sessionJson(claims: SessionClaims | null) {
  if (!claims) {
    return {
      authenticated: false,
      claims: ANONYMOUS_SESSION_CLAIMS,
    };
  }
  return {
    authenticated: true,
    claims,
  };
}

export async function GET(request: NextRequest) {
  const token = normalizeSessionToken(request.cookies.get(SESSION_COOKIE_NAME)?.value);
  const claims = token ? await verifySessionToken(token) : null;
  return NextResponse.json(sessionJson(claims));
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
  const claims = await verifySessionToken(accessToken);
  if (!claims) {
    return NextResponse.json(
      { error_code: "invalid_session_token" },
      { status: 401 },
    );
  }

  const response = NextResponse.json(sessionJson(claims));
  response.cookies.set(buildSessionCookieOptions(request, accessToken));
  return response;
}

export async function DELETE(request: NextRequest) {
  const response = NextResponse.json(sessionJson(null));
  response.cookies.set(buildExpiredSessionCookieOptions(request));
  return response;
}
