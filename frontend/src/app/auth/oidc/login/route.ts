import { NextRequest, NextResponse } from "next/server";

import {
  OIDC_NO_STORE_HEADERS,
  encodeOidcStateCookie,
  oidcStateCookieOptions,
  pkceChallenge,
  randomUrlSafeString,
  safeReturnTo,
  serverOidcConfig,
} from "../shared";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const fetchCache = "force-no-store";

export async function POST(request: NextRequest) {
  const config = serverOidcConfig(request.nextUrl.origin);
  if (!config) {
    return NextResponse.json(
      { error_code: "oidc_browser_configuration_missing" },
      { status: 503, headers: OIDC_NO_STORE_HEADERS },
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  const state = randomUrlSafeString(32);
  const verifier = randomUrlSafeString(64);
  const authorizationUrl = new URL(config.authorizationEndpoint);
  authorizationUrl.searchParams.set("response_type", "code");
  authorizationUrl.searchParams.set("client_id", config.clientId);
  authorizationUrl.searchParams.set("redirect_uri", config.redirectUri);
  authorizationUrl.searchParams.set("scope", config.scope);
  authorizationUrl.searchParams.set("state", state);
  authorizationUrl.searchParams.set("code_challenge", pkceChallenge(verifier));
  authorizationUrl.searchParams.set("code_challenge_method", "S256");

  const returnTo = safeReturnTo(
    body && typeof body === "object"
      ? (body as { return_to?: unknown }).return_to
      : null,
  );
  const response = NextResponse.json(
    { authorization_url: authorizationUrl.toString() },
    { headers: OIDC_NO_STORE_HEADERS },
  );
  response.cookies.set(oidcStateCookieOptions(encodeOidcStateCookie({
    state,
    verifier,
    return_to: returnTo,
  })));
  return response;
}
