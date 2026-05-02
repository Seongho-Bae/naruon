const DEFAULT_BACKEND_URL = "http://localhost:8000";
const SERVER_AUTH_TOKEN_ENV = "API_AUTH_TOKEN";
const SHARED_TOKEN_PROXY_ENV = "API_PROXY_ALLOW_SHARED_TOKEN";
const HOP_BY_HOP_REQUEST_HEADERS = new Set([
  "authorization",
  "connection",
  "content-length",
  "cookie",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);
const HOP_BY_HOP_RESPONSE_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);


function backendBaseUrl(): string {
  return process.env.API_INTERNAL_URL?.trim() || DEFAULT_BACKEND_URL;
}


function serverAuthToken(): string | null {
  return process.env[SERVER_AUTH_TOKEN_ENV]?.trim() || null;
}


function sharedTokenProxyEnabled(): boolean {
  return process.env[SHARED_TOKEN_PROXY_ENV]?.trim().toLowerCase() === "true";
}


export function buildBackendUrl(
  pathSegments: string[],
  search = "",
  baseUrl = backendBaseUrl(),
): URL {
  const encodedPath = pathSegments
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  const normalizedBaseUrl = baseUrl.replace(/\/+$/, "");
  return new URL(`${normalizedBaseUrl}/${encodedPath}${search}`);
}


export function buildProxyHeaders(
  sourceHeaders: Headers,
  token: string,
): Headers {
  const headers = new Headers();
  sourceHeaders.forEach((value, key) => {
    if (!HOP_BY_HOP_REQUEST_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  headers.set("Authorization", `Bearer ${token}`);
  return headers;
}


function responseHeaders(upstreamHeaders: Headers): Headers {
  const headers = new Headers();
  upstreamHeaders.forEach((value, key) => {
    if (!HOP_BY_HOP_RESPONSE_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  return headers;
}


export async function proxyBackendRequest(
  request: Request,
  pathSegments: string[],
): Promise<Response> {
  if (!sharedTokenProxyEnabled()) {
    return new Response("Shared-token backend API proxy is disabled", {
      status: 403,
    });
  }

  const token = serverAuthToken();
  if (!token) {
    return new Response("Backend API authentication is not configured", {
      status: 500,
    });
  }

  const requestUrl = new URL(request.url);
  const init: RequestInit = {
    headers: buildProxyHeaders(request.headers, token),
    method: request.method,
    redirect: "manual",
  };

  if (!new Set(["GET", "HEAD"]).has(request.method.toUpperCase())) {
    init.body = await request.arrayBuffer();
  }

  const upstreamResponse = await fetch(
    buildBackendUrl(pathSegments, requestUrl.search),
    init,
  );
  return new Response(upstreamResponse.body, {
    headers: responseHeaders(upstreamResponse.headers),
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
  });
}
