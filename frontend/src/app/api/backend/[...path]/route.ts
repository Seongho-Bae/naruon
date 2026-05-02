import { proxyBackendRequest } from "@/lib/api-proxy";


type ProxyRouteContext = {
  params: Promise<{ path?: string[] }>;
};


async function handler(request: Request, context: ProxyRouteContext) {
  const params = await context.params;
  return proxyBackendRequest(request, params.path ?? []);
}


export const DELETE = handler;
export const GET = handler;
export const HEAD = handler;
export const PATCH = handler;
export const POST = handler;
export const PUT = handler;
