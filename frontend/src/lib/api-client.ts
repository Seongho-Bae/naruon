type RoleName = 'platform_admin' | 'organization_admin' | 'group_admin' | 'member';

const SCOPED_ROLES: RoleName[] = ['platform_admin', 'organization_admin', 'group_admin', 'member'];

interface RuntimeAuthConfig {
  features?: {
    dev_header_auth_enabled?: boolean;
  };
}

function decodeBearerClaims(token: string): Record<string, unknown> | null {
  const parts = token.split('.');
  if (parts.length < 2) return null;
  try {
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = payload + '='.repeat((4 - (payload.length % 4 || 4)) % 4);
    const decoded = typeof window !== 'undefined'
      ? window.atob(padded)
      : Buffer.from(padded, 'base64').toString('utf-8');
    const claims = JSON.parse(decoded) as Record<string, unknown>;
    const exp = claims.exp;
    if (typeof exp === 'number' && exp <= Math.floor(Date.now() / 1000)) {
      return null;
    }
    return claims;
  } catch {
    return null;
  }
}

function getOrganizationIdClaim(claims: Record<string, unknown> | null) {
  if (typeof claims?.organization_id === 'string' && claims.organization_id.trim()) {
    return claims.organization_id;
  }
  if (typeof claims?.org_id === 'string' && claims.org_id.trim()) {
    return claims.org_id;
  }
  return null;
}

export class ApiClient {
  private baseUrl: string;
  private devHeaderAuthEnabled = false;
  private devHeaderAuthLoaded = false;
  private devHeaderAuthPromise: Promise<void> | null = null;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || (typeof window !== 'undefined' ? '' : 'http://localhost:8000');
  }

  setBaseUrl(url: string) {
    this.baseUrl = url;
    this.devHeaderAuthLoaded = false;
    this.devHeaderAuthPromise = null;
  }

  getBaseUrl() {
    return this.baseUrl;
  }

  private isLocalDevOverrideAllowed() {
    if (typeof window === 'undefined') return false;
    const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    return isLocalHost;
  }

  setDevHeaderAuthEnabled(enabled: boolean) {
    this.devHeaderAuthEnabled = enabled;
    this.devHeaderAuthLoaded = true;
  }

  private async ensureDevHeaderAuthGate(endpoint: string) {
    if (
      endpoint === '/api/runtime-config'
      || typeof window === 'undefined'
      || this.getBearerToken()
      || !this.isLocalDevOverrideAllowed()
      || this.devHeaderAuthLoaded
    ) {
      return;
    }

    if (!this.devHeaderAuthPromise) {
      this.devHeaderAuthPromise = fetch(`${this.baseUrl}/api/runtime-config`, {
        headers: { 'Content-Type': 'application/json' },
      })
        .then(async (response) => {
          if (!response.ok) {
            this.setDevHeaderAuthEnabled(false);
            return;
          }
          const config = await response.json() as RuntimeAuthConfig;
          this.setDevHeaderAuthEnabled(Boolean(config.features?.dev_header_auth_enabled));
        })
        .catch(() => {
          this.setDevHeaderAuthEnabled(false);
        })
        .finally(() => {
          this.devHeaderAuthPromise = null;
        });
    }

    await this.devHeaderAuthPromise;
  }

  private getLocalDevUserId() {
    if (!this.isLocalDevOverrideAllowed() || typeof window === 'undefined') return null;
    const stored = localStorage.getItem('naruon_dev_user')?.trim();
    return stored || 'testuser';
  }

  private getLocalDevRole(): RoleName {
    return this.getLocalDevUserId() === 'admin' ? 'organization_admin' : 'member';
  }

  private getLocalDevOrganizationId() {
    if (!this.isLocalDevOverrideAllowed()) return null;
    return 'org-local-dev';
  }

  canUseManualBearerSession() {
    return this.isLocalDevOverrideAllowed();
  }

  private canUseTrustedLocalDevHeaders() {
    return this.isLocalDevOverrideAllowed() && this.devHeaderAuthLoaded && this.devHeaderAuthEnabled;
  }

  private async getHeaders(endpoint: string, init?: RequestInit): Promise<HeadersInit> {
    await this.ensureDevHeaderAuthGate(endpoint);
    const bearerToken = this.getBearerToken();
    const userId = this.getCurrentUserId();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...init?.headers,
    };
    if (bearerToken) {
      return {
        ...headers,
        Authorization: `Bearer ${bearerToken}`,
      };
    }
    if (userId && this.devHeaderAuthEnabled) {
      const headersWithUser: HeadersInit = {
        ...headers,
        'X-User-Id': userId,
      };
      const organizationId = this.getCurrentOrganizationId();
      if (this.isLocalDevOverrideAllowed() && organizationId) {
        return {
          ...headersWithUser,
          'X-User-Role': this.getCurrentRole(),
          'X-Organization-Id': organizationId,
        };
      }
      return headersWithUser;
    }
    return headers;
  }

  getCurrentUserId() {
    const claims = this.getSessionClaims();
    if (claims?.sub && typeof claims.sub === 'string') {
      return claims.sub;
    }
    return this.getLocalDevUserId();
  }

  getCurrentRole(): RoleName {
    const claims = this.getSessionClaims();
    const requestedRole = claims?.naruon_role ?? claims?.role;
    if (typeof requestedRole === 'string' && SCOPED_ROLES.includes(requestedRole as RoleName)) {
      return requestedRole as RoleName;
    }

    const roles = claims?.roles;
    if (Array.isArray(roles)) {
      for (const candidate of SCOPED_ROLES) {
        if (roles.includes(candidate)) {
          return candidate;
        }
      }
      return 'member';
    }

    if (claims) {
      return 'member';
    }

    return this.getLocalDevRole();
  }

  getCurrentOrganizationId() {
    const claims = this.getSessionClaims();
    const organizationId = getOrganizationIdClaim(claims);
    if (organizationId) return organizationId;
    return this.getLocalDevOrganizationId();
  }

  canManageWorkspaceSettings() {
    const claims = this.getSessionClaims();
    if (!claims && !this.canUseTrustedLocalDevHeaders()) {
      return false;
    }

    const role = claims ? this.getCurrentRole() : this.getLocalDevRole();
    const organizationId = claims ? getOrganizationIdClaim(claims) : this.getLocalDevOrganizationId();
    return (role === 'platform_admin' || role === 'organization_admin') && !!organizationId;
  }

  isWorkspaceSettingsAccessReady() {
    if (this.getSessionClaims()) return true;
    if (!this.isLocalDevOverrideAllowed()) return true;
    return this.devHeaderAuthLoaded;
  }

  async ensureWorkspaceSettingsAccessReady() {
    await this.ensureDevHeaderAuthGate('/api/workspace-settings-access');
  }

  getBearerToken() {
    if (typeof window === 'undefined') return null;
    const token = localStorage.getItem('naruon_bearer_token')?.trim();
    if (!token) return null;
    const claims = decodeBearerClaims(token);
    if (!claims) {
      localStorage.removeItem('naruon_bearer_token');
      return null;
    }
    return token;
  }

  setBearerToken(token: string) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('naruon_bearer_token', token.trim());
  }

  clearBearerToken() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('naruon_bearer_token');
  }

  getSessionClaims(): Record<string, unknown> | null {
    const token = this.getBearerToken();
    if (!token) return null;
    return decodeBearerClaims(token);
  }

  async get<T>(endpoint: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...init,
      headers: await this.getHeaders(endpoint, init),
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
      headers: await this.getHeaders(endpoint, init),
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
      headers: await this.getHeaders(endpoint, init),
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

  async patch<T>(endpoint: string, body: unknown, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...init,
      method: 'PATCH',
      headers: await this.getHeaders(endpoint, init),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const error = new Error(`API PATCH ${endpoint} failed: ${response.status} ${response.statusText}`) as Error & { status?: number };
      error.status = response.status;
      throw error;
    }
    const text = await response.text();
    return text ? JSON.parse(text) : ({} as T);
  }

  async delete<T>(endpoint: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...init,
      method: 'DELETE',
      headers: await this.getHeaders(endpoint, init),
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
