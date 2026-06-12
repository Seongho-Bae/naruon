/* @vitest-environment jsdom */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  buildOidcAuthorizationUrl,
  clearOidcSession,
  completeOidcRedirect,
  getOidcBrowserConfig,
  startOidcLogin,
} from './oidc-session';

function installCrypto() {
  const cryptoMock = {
    getRandomValues: (bytes: Uint8Array) => {
      bytes.fill(7);
      return bytes;
    },
    subtle: {
      digest: vi.fn(async () => new Uint8Array([1, 2, 3, 4]).buffer),
    },
  };
  Object.defineProperty(window, 'crypto', {
    configurable: true,
    value: cryptoMock,
  });
}

describe('oidc-session', () => {
  beforeEach(() => {
    installCrypto();
    vi.stubEnv('NEXT_PUBLIC_OIDC_ISSUER_URL', 'https://login.example.com/realms/naruon/');
    vi.stubEnv('NEXT_PUBLIC_OIDC_CLIENT_ID', 'naruon-web');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('derives Keycloak endpoints from public OIDC settings', () => {
    const config = getOidcBrowserConfig('https://app.example.com');

    expect(config).toMatchObject({
      issuerUrl: 'https://login.example.com/realms/naruon',
      clientId: 'naruon-web',
      redirectUri: 'https://app.example.com/auth/callback',
      authorizationEndpoint: 'https://login.example.com/realms/naruon/protocol/openid-connect/auth',
      tokenEndpoint: 'https://login.example.com/realms/naruon/protocol/openid-connect/token',
      endSessionEndpoint: 'https://login.example.com/realms/naruon/protocol/openid-connect/logout',
    });
  });

  it('builds a PKCE authorization request and stores transient login state', async () => {
    const assignedUrls: string[] = [];

    await startOidcLogin({
      returnTo: '/settings',
      navigate: (url) => assignedUrls.push(url),
    });

    expect(sessionStorage.getItem('naruon_oidc_state')).toBeTruthy();
    expect(sessionStorage.getItem('naruon_oidc_pkce_verifier')).toBeTruthy();
    expect(sessionStorage.getItem('naruon_oidc_return_to')).toBe('/settings');
    const authorizationUrl = new URL(assignedUrls[0]);
    expect(authorizationUrl.origin).toBe('https://login.example.com');
    expect(authorizationUrl.searchParams.get('response_type')).toBe('code');
    expect(authorizationUrl.searchParams.get('client_id')).toBe('naruon-web');
    expect(authorizationUrl.searchParams.get('code_challenge_method')).toBe('S256');
    expect(authorizationUrl.searchParams.get('code_challenge')).toBe('AQIDBA');
  });

  it('exchanges a valid OIDC callback code and stores the bearer session token', async () => {
    sessionStorage.setItem('naruon_oidc_state', 'state-123');
    sessionStorage.setItem('naruon_oidc_pkce_verifier', 'verifier-123');
    sessionStorage.setItem('naruon_oidc_return_to', '/security');
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ access_token: 'oidc.jwt.token' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })));

    const result = await completeOidcRedirect('?code=auth-code&state=state-123');

    expect(result.returnTo).toBe('/security');
    expect(localStorage.getItem('naruon_session_token')).toBe('oidc.jwt.token');
    expect(sessionStorage.getItem('naruon_oidc_state')).toBeNull();
    const tokenCall = vi.mocked(fetch).mock.calls[0];
    expect(tokenCall[0]).toBe('https://login.example.com/realms/naruon/protocol/openid-connect/token');
    expect(String(tokenCall[1]?.body)).toContain('grant_type=authorization_code');
    expect(String(tokenCall[1]?.body)).toContain('code_verifier=verifier-123');
  });

  it('revokes the backend session, clears local state, and redirects to the provider logout endpoint', async () => {
    localStorage.setItem('naruon_session_token', 'oidc.jwt.token');
    sessionStorage.setItem('naruon_oidc_state', 'state-123');
    const assignedUrls: string[] = [];
    vi.stubGlobal('fetch', vi.fn(async () => new Response(null, { status: 200 })));

    await clearOidcSession({
      postLogoutRedirectUri: 'https://app.example.com',
      navigate: (url) => assignedUrls.push(url),
    });

    expect(fetch).toHaveBeenCalledWith('/api/auth/logout', {
      method: 'POST',
      headers: {
        Authorization: 'Bearer oidc.jwt.token',
      },
    });
    expect(localStorage.getItem('naruon_session_token')).toBeNull();
    expect(sessionStorage.getItem('naruon_oidc_state')).toBeNull();
    const logoutUrl = new URL(assignedUrls[0]);
    expect(logoutUrl.toString()).toContain('/protocol/openid-connect/logout');
    expect(logoutUrl.searchParams.get('client_id')).toBe('naruon-web');
    expect(logoutUrl.searchParams.get('post_logout_redirect_uri')).toBe('https://app.example.com');
  });

  it('builds an authorization URL directly for deterministic callers', async () => {
    const config = getOidcBrowserConfig('https://app.example.com');
    expect(config).toBeTruthy();

    const authorizationUrl = await buildOidcAuthorizationUrl(config!, 'state-123', 'verifier-123');

    expect(new URL(authorizationUrl).searchParams.get('state')).toBe('state-123');
  });
});
