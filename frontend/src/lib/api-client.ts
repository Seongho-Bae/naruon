export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    // If constructed without URL, fallback to relative path or safe dev URL
    this.baseUrl = baseUrl || (typeof window !== 'undefined' ? '' : 'http://localhost:8000');
  }

  setBaseUrl(url: string) {
    this.baseUrl = url;
  }

  getBaseUrl() {
    return this.baseUrl;
  }

  async get<T>(endpoint: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        // In real system, proper token is included
        'X-User-Id': 'testuser',
        ...init?.headers,
      },
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
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': 'testuser',
        ...init?.headers,
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`API POST ${endpoint} failed: ${response.statusText}`);
    }
    return response.json();
  }
}

// Global default client instance
export const apiClient = new ApiClient();
