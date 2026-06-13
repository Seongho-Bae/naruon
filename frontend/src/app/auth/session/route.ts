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
export const dynamic = "force-dynamic";
export const fetchCache = "force-no-store";

const STATE_CHANGING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const NO_STORE_HEADERS = {
  "Cache-Control": "no-store",
};

function sameOriginStateChangingRequest(request: NextRequest): boolean {
  if (!STATE_CHANGING_METHODS.has(request.method.toUpperCase())) return true;

  const fetchSite = request.headers.get("sec-fetch-site")?.trim().toLowerCase();
  if (fetchSite === "cross-site") return false;

  const origin = request.headers.get("origin");
  if (!origin) return true;

  try {
    return new URL(origin).origin === request.nextUrl.origin;
  } catch {
    return false;
  }
}

function csrfRejectedResponse() {
  return NextResponse.json(
    {
      error_code: "csrf_origin_rejected",
      message: "Cross-site session updates are not allowed",
    },
    {
      status: 403,
      headers: {
        "Referrer-Policy": "no-referrer",
      },
    },
  );
}

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
  const organizationId = stringClaim(body.organization_id);
  const workspaceId = stringClaim(body.workspace_id);
  if (!userId || !organizationId || !workspaceId) return null;
  return {
    userId,
    organizationId,
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
  return NextResponse.json(sessionJson(claims), { headers: NO_STORE_HEADERS });
}

export async function POST(request: NextRequest) {
  if (!sameOriginStateChangingRequest(request)) {
    return csrfRejectedResponse();
  }

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

  const response = NextResponse.json(sessionJson(claims), {
    headers: NO_STORE_HEADERS,
  });
  // Do not promote an existing browser cookie; install only the backend-verified
  // bearer session supplied in this request, replacing any previous session id.
  response.cookies.set(buildSessionCookieOptions(accessToken));
  return response;
}

export async function DELETE(request: NextRequest) {
  if (!sameOriginStateChangingRequest(request)) {
    return csrfRejectedResponse();
  }

  const response = NextResponse.json(sessionJson(null), { headers: NO_STORE_HEADERS });
  response.cookies.set(buildExpiredSessionCookieOptions());
  return response;
}
