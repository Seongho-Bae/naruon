export interface OidcBrowserConfig {
  issuerUrl: string;
  clientId: string;
  redirectUri: string;
  scope: string;
  authorizationEndpoint: string;
  tokenEndpoint: string;
  endSessionEndpoint: string;
}

export interface OidcLoginOptions {
  returnTo?: string;
  navigate?: (url: string) => void;
}

export interface OidcLogoutOptions {
  postLogoutRedirectUri?: string;
  navigate?: (url: string) => void;
}

const OIDC_STATE_KEY = 'naruon_oidc_state';
const OIDC_VERIFIER_KEY = 'naruon_oidc_pkce_verifier';
const OIDC_RETURN_TO_KEY = 'naruon_oidc_return_to';
const DEFAULT_OIDC_SCOPE = 'openid profile email';

export class OidcSessionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'OidcSessionError';
  }
}

async function persistOidcSession(accessToken: string) {
  const response = await fetch('/auth/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ access_token: accessToken }),
  });
  if (!response.ok) {
    throw new OidcSessionError('OIDC session persistence failed');
  }
}

async function clearPersistedOidcSession() {
  const response = await fetch('/auth/session', {
    method: 'DELETE',
    credentials: 'same-origin',
  });
  if (!response.ok) {
    throw new OidcSessionError('OIDC session clear failed');
  }
}

function envValue(name: string): string | null {
  const value = process.env[name]?.trim();
  return value ? value : null;
}

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, '');
}

function defaultBrowserOrigin() {
  if (typeof window === 'undefined') return '';
  return window.location.origin;
}

function defaultRedirectUri(origin: string) {
  return origin ? `${origin}/auth/callback` : '/auth/callback';
}

export function getOidcBrowserConfig(origin = defaultBrowserOrigin()): OidcBrowserConfig | null {
  const issuerUrl = envValue('NEXT_PUBLIC_OIDC_ISSUER_URL');
  const clientId = envValue('NEXT_PUBLIC_OIDC_CLIENT_ID');
  if (!issuerUrl || !clientId) return null;

  const normalizedIssuer = trimTrailingSlash(issuerUrl);
  const keycloakEndpointBase = `${normalizedIssuer}/protocol/openid-connect`;
  return {
    issuerUrl: normalizedIssuer,
    clientId,
    redirectUri: envValue('NEXT_PUBLIC_OIDC_REDIRECT_URI') ?? defaultRedirectUri(origin),
    scope: envValue('NEXT_PUBLIC_OIDC_SCOPE') ?? DEFAULT_OIDC_SCOPE,
    authorizationEndpoint: envValue('NEXT_PUBLIC_OIDC_AUTHORIZATION_ENDPOINT') ?? `${keycloakEndpointBase}/auth`,
    tokenEndpoint: envValue('NEXT_PUBLIC_OIDC_TOKEN_ENDPOINT') ?? `${keycloakEndpointBase}/token`,
    endSessionEndpoint: envValue('NEXT_PUBLIC_OIDC_END_SESSION_ENDPOINT') ?? `${keycloakEndpointBase}/logout`,
  };
}

function requireBrowserStorage() {
  if (typeof window === 'undefined') {
    throw new OidcSessionError('OIDC browser session storage is unavailable');
  }
}

function randomUrlSafeString(byteLength: number) {
  requireBrowserStorage();
  const bytes = new Uint8Array(byteLength);
  window.crypto.getRandomValues(bytes);
  return base64UrlEncode(bytes);
}

function base64UrlEncode(bytes: Uint8Array) {
  let binary = '';
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function pkceChallenge(verifier: string) {
  requireBrowserStorage();
  const encoded = new TextEncoder().encode(verifier);
  const digest = await window.crypto.subtle.digest('SHA-256', encoded);
  return base64UrlEncode(new Uint8Array(digest));
}

export async function buildOidcAuthorizationUrl(config: OidcBrowserConfig, state: string, verifier: string) {
  const challenge = await pkceChallenge(verifier);
  const authorizationUrl = new URL(config.authorizationEndpoint);
  authorizationUrl.searchParams.set('response_type', 'code');
  authorizationUrl.searchParams.set('client_id', config.clientId);
  authorizationUrl.searchParams.set('redirect_uri', config.redirectUri);
  authorizationUrl.searchParams.set('scope', config.scope);
  authorizationUrl.searchParams.set('state', state);
  authorizationUrl.searchParams.set('code_challenge', challenge);
  authorizationUrl.searchParams.set('code_challenge_method', 'S256');
  return authorizationUrl.toString();
}

export async function startOidcLogin(options: OidcLoginOptions = {}) {
  requireBrowserStorage();
  const config = getOidcBrowserConfig();
  if (!config) {
    throw new OidcSessionError('OIDC browser configuration is missing');
  }

  const state = randomUrlSafeString(32);
  const verifier = randomUrlSafeString(64);
  window.sessionStorage.setItem(OIDC_STATE_KEY, state);
  window.sessionStorage.setItem(OIDC_VERIFIER_KEY, verifier);
  window.sessionStorage.setItem(OIDC_RETURN_TO_KEY, options.returnTo ?? window.location.pathname);

  const authorizationUrl = await buildOidcAuthorizationUrl(config, state, verifier);
  const navigate = options.navigate ?? ((url: string) => window.location.assign(url));
  navigate(authorizationUrl);
}

export async function completeOidcRedirect(search = window.location.search) {
  requireBrowserStorage();
  const config = getOidcBrowserConfig();
  if (!config) {
    throw new OidcSessionError('OIDC browser configuration is missing');
  }

  const params = new URLSearchParams(search);
  const providerError = params.get('error');
  if (providerError) {
    throw new OidcSessionError(providerError);
  }

  const code = params.get('code');
  const state = params.get('state');
  const expectedState = window.sessionStorage.getItem(OIDC_STATE_KEY);
  const verifier = window.sessionStorage.getItem(OIDC_VERIFIER_KEY);
  if (!code || !state || !expectedState || state !== expectedState || !verifier) {
    throw new OidcSessionError('OIDC callback state is invalid');
  }

  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: config.clientId,
    code,
    code_verifier: verifier,
    redirect_uri: config.redirectUri,
  });
  const response = await fetch(config.tokenEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!response.ok) {
    throw new OidcSessionError('OIDC token exchange failed');
  }
  const tokenBody = await response.json() as { access_token?: unknown };
  const accessToken = typeof tokenBody.access_token === 'string' ? tokenBody.access_token.trim() : '';
  if (!accessToken) {
    throw new OidcSessionError('OIDC token response did not include an access token');
  }

  await persistOidcSession(accessToken);
  const returnTo = window.sessionStorage.getItem(OIDC_RETURN_TO_KEY) || '/';
  clearOidcTransientState();
  return { returnTo };
}

export function clearOidcTransientState() {
  if (typeof window === 'undefined') return;
  window.sessionStorage.removeItem(OIDC_STATE_KEY);
  window.sessionStorage.removeItem(OIDC_VERIFIER_KEY);
  window.sessionStorage.removeItem(OIDC_RETURN_TO_KEY);
}

export async function clearOidcSession(options: OidcLogoutOptions = {}) {
  requireBrowserStorage();
  const config = getOidcBrowserConfig();
  await clearPersistedOidcSession();
  clearOidcTransientState();

  if (!config) return;
  const postLogoutRedirectUri = options.postLogoutRedirectUri ?? window.location.origin;
  const logoutUrl = new URL(config.endSessionEndpoint);
  logoutUrl.searchParams.set('client_id', config.clientId);
  logoutUrl.searchParams.set('post_logout_redirect_uri', postLogoutRedirectUri);
  const navigate = options.navigate ?? ((url: string) => window.location.assign(url));
  navigate(logoutUrl.toString());
}
