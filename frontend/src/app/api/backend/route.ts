import {
  pathSegmentsFromProxyPath,
  proxyBackendRequest,
} from "@/lib/api-proxy";


async function handler(request: Request) {
  const requestUrl = new URL(request.url);
  const pathSegments = pathSegmentsFromProxyPath(requestUrl.searchParams.get("path"));
  if (!pathSegments) {
    return new Response("Backend API path is required", { status: 400 });
  }

  requestUrl.searchParams.delete("path");
  return proxyBackendRequest(request, pathSegments, requestUrl.search);
}


export const DELETE = handler;
export const GET = handler;
export const HEAD = handler;
export const PATCH = handler;
export const POST = handler;
export const PUT = handler;
