const CLIENT_CONTROLLED_AUTHORITY_HEADERS = new Set([
  'authorization',
  'x-dev-auth-token',
  'x-group-id',
  'x-group-ids',
  'x-organization-id',
  'x-user-id',
  'x-user-role',
]);

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || (typeof window !== 'undefined' ? '' : 'http://localhost:8000');
  }

  setBaseUrl(url: string) {
    this.baseUrl = url;
  }

  getBaseUrl() {
    return this.baseUrl;
  }

  private getHeaders(init?: RequestInit): HeadersInit {
    const sessionToken = this.getSessionToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...this.getSafeCallerHeaders(init?.headers),
    };
    if (sessionToken) {
      return {
        ...headers,
        Authorization: `Bearer ${sessionToken}`,
      };
    }
    return headers;
  }

  private getSafeCallerHeaders(headers?: HeadersInit): Record<string, string> {
    const safeHeaders: Record<string, string> = {};
    const includeHeader = (name: string, value: string) => {
      if (CLIENT_CONTROLLED_AUTHORITY_HEADERS.has(name.toLowerCase())) return;
      safeHeaders[name] = value;
    };

    if (!headers) return safeHeaders;
    if (typeof Headers !== 'undefined' && headers instanceof Headers) {
      headers.forEach((value, name) => includeHeader(name, value));
      return safeHeaders;
    }
    if (Array.isArray(headers)) {
      headers.forEach(([name, value]) => includeHeader(name, value));
      return safeHeaders;
    }

    Object.entries(headers).forEach(([name, value]) => includeHeader(name, value));
    return safeHeaders;
  }

  getSessionToken() {
    if (typeof window === 'undefined') return null;

    const stored = localStorage.getItem('naruon_session_token')?.trim();
    return stored || null;
  }

  getCurrentUserId() {
    const sessionToken = this.getSessionToken();
    if (!sessionToken) return null;

    const [, payloadSegment] = sessionToken.split('.');
    if (!payloadSegment) return null;

    try {
      const normalizedPayload = payloadSegment.replace(/-/g, '+').replace(/_/g, '/');
      const paddedPayload = normalizedPayload.padEnd(
        Math.ceil(normalizedPayload.length / 4) * 4,
        '=',
      );
      const decodedPayload = JSON.parse(atob(paddedPayload)) as { sub?: unknown };
      if (typeof decodedPayload.sub !== 'string') return null;
      return decodedPayload.sub.trim() || null;
    } catch {
      return null;
    }
  }

  async get<T>(endpoint: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...init,
      headers: this.getHeaders(init),
    });
    if (!response.ok) {
      const error = new Error(`API GET ${endpoint} failed: ${response.status} ${response.statusText}`) as Error & { status?: number };
      error.status = response.status;
      throw error;
    }
    return response.json();
  }

  async post<T>(endpoint: string, body: unknown, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...init,
      method: 'POST',
      headers: this.getHeaders(init),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const error = new Error(`API POST ${endpoint} failed: ${response.status} ${response.statusText}`) as Error & { status?: number };
      error.status = response.status;
      throw error;
    }
    return response.json();
  }

  async put<T>(endpoint: string, body: unknown, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...init,
      method: 'PUT',
      headers: this.getHeaders(init),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const error = new Error(`API PUT ${endpoint} failed: ${response.status} ${response.statusText}`) as Error & { status?: number };
      error.status = response.status;
      throw error;
    }
    // PUT might return 204 No Content
    const text = await response.text();
    return text ? JSON.parse(text) : ({} as T);
  }

  async delete<T>(endpoint: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...init,
      method: 'DELETE',
      headers: this.getHeaders(init),
    });
    if (!response.ok) {
      const error = new Error(`API DELETE ${endpoint} failed: ${response.status} ${response.statusText}`) as Error & { status?: number };
      error.status = response.status;
      throw error;
    }
    // DELETE might return 204 No Content, handle gracefully
    const text = await response.text();
    return text ? JSON.parse(text) : ({} as T);
  }
}

export const apiClient = new ApiClient();
