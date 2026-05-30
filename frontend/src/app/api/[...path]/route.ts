import { NextRequest, NextResponse } from "next/server";

import { backendApiBaseUrl } from "@/lib/backend-url";

export const runtime = "nodejs";

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

type ApiRouteContext = {
  params: Promise<{ path?: string[] }> | { path?: string[] };
};

function filteredRequestHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  request.headers.forEach((value, name) => {
    const lowerName = name.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(lowerName)) return;
    if (CLIENT_AUTHORITY_HEADERS.has(lowerName)) return;
    headers.set(name, value);
  });
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

async function proxyApiRequest(
  request: NextRequest,
  context: ApiRouteContext,
): Promise<NextResponse> {
  const params = await context.params;
  const path = params.path ?? [];
  const target = backendApiBaseUrl();
  target.pathname = `/api/${path.map(encodeURIComponent).join("/")}`;
  target.search = request.nextUrl.search;

  const init: RequestInit = {
    method: request.method,
    headers: filteredRequestHeaders(request),
    redirect: "manual",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  const response = await fetch(target, init);
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
