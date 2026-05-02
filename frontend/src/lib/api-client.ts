export const BACKEND_PROXY_PREFIX = "/api/backend";


export function backendApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${BACKEND_PROXY_PREFIX}${normalizedPath}`;
}


function normalizeHeaders(headers?: HeadersInit): Record<string, string> {
  if (!headers) return {};
  if (headers instanceof Headers) {
    return Object.fromEntries(headers.entries());
  }
  if (Array.isArray(headers)) {
    return Object.fromEntries(headers);
  }
  return { ...headers };
}


export function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const headers = normalizeHeaders(init.headers);
  const hasHeaders = Object.keys(headers).length > 0;
  const hasInit = Object.keys(init).some((key) => key !== 'headers');

  if (!hasHeaders && !hasInit) {
    return fetch(input);
  }

  return fetch(input, {
    ...init,
    ...(hasHeaders ? { headers } : {}),
  });
}
