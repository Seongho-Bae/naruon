/* @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ApiClient } from './api-client';

function createUnsignedToken(payload: Record<string, unknown>) {
  const encoded = window.btoa(JSON.stringify(payload)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  return `header.${encoded}.signature`;
}

describe('ApiClient', () => {
  const originalLocation = window.location;

  afterEach(() => {
    window.localStorage.clear();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
    vi.unstubAllGlobals();
  });

  it('does not allow dev-header fallback identities on non-local hosts without a bearer token', () => {
    window.localStorage.setItem('naruon_dev_user', 'member-1');
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('https://app.example.com/settings'),
    });

    const client = new ApiClient('');

    expect(client.getCurrentUserId()).toBeNull();
  });

  it('allows local-host dev fallback identities when no bearer token is present', () => {
    window.localStorage.setItem('naruon_dev_user', 'admin');
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('http://localhost/settings'),
    });

    const client = new ApiClient('');

    expect(client.getCurrentUserId()).toBe('admin');
  });

  it('treats bearer tokens without trusted admin role claims as member access', () => {
    window.localStorage.setItem('naruon_bearer_token', createUnsignedToken({ sub: 'admin' }));

    const client = new ApiClient('');

    expect(client.getCurrentRole()).toBe('member');
  });

  it('does not send dev headers while reading the runtime-config gate', async () => {
    window.localStorage.setItem('naruon_dev_user', 'admin');
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('http://localhost/settings'),
    });

    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({}),
    }));
    vi.stubGlobal('fetch', fetchMock);

    const client = new ApiClient('');
    await client.get('/api/runtime-config');

    const headers = fetchMock.mock.calls[0]?.[1]?.headers as Record<string, string>;
    expect(headers['X-User-Id']).toBeUndefined();
    expect(headers['X-User-Role']).toBeUndefined();
    expect(headers['X-Organization-Id']).toBeUndefined();
  });

  it('sends scoped dev headers only after runtime config enables trusted header auth', async () => {
    window.localStorage.setItem('naruon_dev_user', 'admin');
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('http://localhost/settings'),
    });

    const fetchMock = vi.fn(async (url: string) => {
      if (url === '/api/runtime-config') {
        return {
          ok: true,
          json: async () => ({
            features: {
              dev_header_auth_enabled: true,
            },
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({}),
      };
    });
    vi.stubGlobal('fetch', fetchMock);

    const client = new ApiClient('');
    await client.get('/api/emails');

    const runtimeHeaders = fetchMock.mock.calls[0]?.[1]?.headers as Record<string, string>;
    const apiHeaders = fetchMock.mock.calls[1]?.[1]?.headers as Record<string, string>;
    expect(runtimeHeaders['X-User-Id']).toBeUndefined();
    expect(apiHeaders['X-User-Id']).toBe('admin');
    expect(apiHeaders['X-User-Role']).toBe('organization_admin');
    expect(apiHeaders['X-Organization-Id']).toBe('org-local-dev');
  });

  it('does not send localhost dev headers when runtime config disables trusted header auth', async () => {
    window.localStorage.setItem('naruon_dev_user', 'admin');
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('http://localhost/settings'),
    });

    const fetchMock = vi.fn(async (url: string) => {
      if (url === '/api/runtime-config') {
        return {
          ok: true,
          json: async () => ({
            features: {
              dev_header_auth_enabled: false,
            },
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({}),
      };
    });
    vi.stubGlobal('fetch', fetchMock);

    const client = new ApiClient('');
    await client.get('/api/emails');

    const apiHeaders = fetchMock.mock.calls[1]?.[1]?.headers as Record<string, string>;
    expect(apiHeaders['X-User-Id']).toBeUndefined();
    expect(apiHeaders['X-User-Role']).toBeUndefined();
    expect(apiHeaders['X-Organization-Id']).toBeUndefined();
  });

  it('treats expired bearer tokens as absent so localhost dev fallback can recover', async () => {
    window.localStorage.setItem('naruon_dev_user', 'admin');
    window.localStorage.setItem('naruon_bearer_token', createUnsignedToken({
      sub: 'admin',
      exp: Math.floor(Date.now() / 1000) - 60,
    }));
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('http://localhost/settings'),
    });

    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({}),
    }));
    vi.stubGlobal('fetch', fetchMock);

    const client = new ApiClient('');
    await client.get('/api/runtime-config');

    expect(client.getSessionClaims()).toBeNull();
    expect(client.getCurrentUserId()).toBe('admin');
    const headers = fetchMock.mock.calls[0]?.[1]?.headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
    expect(headers['X-User-Id']).toBeUndefined();
  });
});
