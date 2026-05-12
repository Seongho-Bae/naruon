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
    // Check localStorage for a dev user override, fallback to testuser
    let userId = 'testuser';
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('naruon_dev_user');
      if (stored) userId = stored;
    }

    return {
      'Content-Type': 'application/json',
      'X-User-Id': userId,
      ...init?.headers,
    };
  }

  async get<T>(endpoint: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...init,
      headers: this.getHeaders(init),
    });
    if (!response.ok) {
      throw new Error(`API GET ${endpoint} failed: ${response.statusText}`);
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
      throw new Error(`API POST ${endpoint} failed: ${response.statusText}`);
    }
    return response.json();
  }
}

export const apiClient = new ApiClient();
