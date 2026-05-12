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
    const userId = this.getCurrentUserId();

    return {
      'Content-Type': 'application/json',
      'X-User-Id': userId,
      'X-Workspace-Id': this.getCurrentWorkspaceId(),
      'X-User-Role': this.getCurrentUserRole(),
      ...init?.headers,
    };
  }

  getCurrentUserId() {
    const fallbackUserId = 'testuser';
    if (typeof window === 'undefined') return fallbackUserId;

    const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    const isPrivateLan = window.location.hostname.startsWith('192.168.');
    const allowDevOverride = process.env.NODE_ENV !== 'production' || isLocalHost || isPrivateLan;
    if (!allowDevOverride) return fallbackUserId;

    const stored = localStorage.getItem('naruon_dev_user')?.trim();
    return stored || fallbackUserId;
  }

  getCurrentWorkspaceId() {
    const fallbackWorkspaceId = 'default-workspace';
    if (typeof window === 'undefined') return fallbackWorkspaceId;

    const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    const isPrivateLan = window.location.hostname.startsWith('192.168.');
    const allowDevOverride = process.env.NODE_ENV !== 'production' || isLocalHost || isPrivateLan;
    if (!allowDevOverride) return fallbackWorkspaceId;

    const stored = localStorage.getItem('naruon_dev_workspace')?.trim();
    return stored || fallbackWorkspaceId;
  }

  getCurrentUserRole() {
    return this.getCurrentUserId() === 'admin' ? 'organization_admin' : 'member';
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
