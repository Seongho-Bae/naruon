export function buildApiHeaders(headers?: HeadersInit): Headers {
  const nextHeaders = new Headers(headers);
  const localToken = process.env.NEXT_PUBLIC_API_AUTH_TOKEN?.trim();

  if (localToken && !nextHeaders.has('Authorization')) {
    nextHeaders.set('Authorization', `Bearer ${localToken}`);
  }

  return nextHeaders;
}

export function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  return fetch(input, {
    ...init,
    headers: buildApiHeaders(init.headers),
  });
}
