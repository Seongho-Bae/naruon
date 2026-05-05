export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getApiAuthToken(): string {
  return process.env.NEXT_PUBLIC_API_AUTH_TOKEN?.trim() || "";
}

export function buildApiHeaders(headers?: HeadersInit): Headers {
  const apiHeaders = new Headers(headers);
  const apiAuthToken = getApiAuthToken();

  if (apiAuthToken) {
    apiHeaders.set("Authorization", `Bearer ${apiAuthToken}`);
  }

  return apiHeaders;
}

export function apiFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  return fetch(input, {
    ...init,
    headers: buildApiHeaders(init.headers),
  });
}
