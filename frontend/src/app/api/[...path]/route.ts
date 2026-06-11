import { NextRequest, NextResponse } from "next/server";

import { backendApiBaseUrl } from "@/lib/backend-url";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const fetchCache = "force-no-store";

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

const CLIENT_AUTHORITY_HEADERS = new Set([
  "x-dev-auth-token",
  "x-group-id",
  "x-group-ids",
  "x-organization-id",
  "x-user-id",
  "x-user-role",
]);

const ALLOWED_BACKEND_QUERY_PARAMS = new Set([
  "folder",
  "limit",
  "source_message_id",
  "source_thread_id",
]);
const MAX_QUERY_PARAM_COUNT = 12;
const MAX_QUERY_PARAM_VALUE_LENGTH = 2048;
const CONTROL_CHARACTER_PATTERN = /[\u0000-\u001f\u007f]/;

type ApiRouteContext = {
  params: Promise<{ path?: string[] }> | { path?: string[] };
};

class InvalidProxyQueryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidProxyQueryError";
  }
}

function filteredRequestHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  request.headers.forEach((value, name) => {
    const lowerName = name.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(lowerName)) return;
    if (CLIENT_AUTHORITY_HEADERS.has(lowerName)) return;
    headers.set(name, value);
  });

  // Inject session token from HttpOnly cookie into Authorization header if missing
  if (!headers.has("authorization")) {
    const sessionCookie = request.cookies.get("naruon_session_token");
    if (sessionCookie?.value) {
      headers.set("authorization", `Bearer ${sessionCookie.value}`);
    }
  }

  return headers;
}

function filteredResponseHeaders(response: Response): Headers {
  const headers = new Headers();
  response.headers.forEach((value, name) => {
    if (HOP_BY_HOP_HEADERS.has(name.toLowerCase())) return;
    headers.set(name, value);
  });
  return headers;
}

function safeBackendQuery(searchParams: URLSearchParams): string {
  const forwardedParams = new URLSearchParams();
  const seenNames = new Set<string>();
  let paramCount = 0;

  for (const [name, value] of searchParams) {
    paramCount += 1;
    if (paramCount > MAX_QUERY_PARAM_COUNT) {
      throw new InvalidProxyQueryError("Too many query parameters");
    }
    if (!ALLOWED_BACKEND_QUERY_PARAMS.has(name)) {
      throw new InvalidProxyQueryError(`Unsupported query parameter: ${name}`);
    }
    if (seenNames.has(name)) {
      throw new InvalidProxyQueryError(`Duplicate query parameter: ${name}`);
    }
    if (
      value.length > MAX_QUERY_PARAM_VALUE_LENGTH ||
      CONTROL_CHARACTER_PATTERN.test(value)
    ) {
      throw new InvalidProxyQueryError(`Invalid query parameter value: ${name}`);
    }
    seenNames.add(name);
    forwardedParams.set(name, value);
  }

  const query = forwardedParams.toString();
  return query ? `?${query}` : "";
}

async function proxyApiRequest(
  request: NextRequest,
  context: ApiRouteContext,
): Promise<NextResponse> {
  const params = await context.params;
  const path = params.path ?? [];
  const target = backendApiBaseUrl();
  target.pathname = `/api/${path.map(encodeURIComponent).join("/")}`;
  try {
    target.search = safeBackendQuery(request.nextUrl.searchParams);
  } catch (error) {
    if (error instanceof InvalidProxyQueryError) {
      return NextResponse.json(
        {
          error_code: "invalid_proxy_query",
          message: error.message,
        },
        {
          status: 400,
          headers: {
            "Referrer-Policy": "no-referrer",
          },
        },
      );
    }
    throw error;
  }

  const init: RequestInit = {
    method: request.method,
    headers: filteredRequestHeaders(request),
    redirect: "manual",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }


  let response: Response;
  try {
    response = await fetch(target, init);
  } catch (error) {
    // If the backend isn't available (e.g. during build), return a 503 instead of throwing
    console.error("Proxy fetch failed:", error);
    return new NextResponse(null, { status: 503, statusText: "Service Unavailable" });
  }

  return new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: filteredResponseHeaders(response),
  });
}

export async function GET(request: NextRequest, context: ApiRouteContext) {
  return proxyApiRequest(request, context);
}

export async function POST(request: NextRequest, context: ApiRouteContext) {
  return proxyApiRequest(request, context);
}

export async function PUT(request: NextRequest, context: ApiRouteContext) {
  return proxyApiRequest(request, context);
}

export async function PATCH(request: NextRequest, context: ApiRouteContext) {
  return proxyApiRequest(request, context);
}

export async function DELETE(request: NextRequest, context: ApiRouteContext) {
  return proxyApiRequest(request, context);
}
