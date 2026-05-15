/* @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ApiClient } from './api-client';

function createUnsignedToken(payload: Record<string, unknown>) {
  const encoded = window.btoa(JSON.stringify(payload)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  return `header.${encoded}.signature`;
}

function headersForCall(fetchMock: { mock: { calls: unknown[][] } }, index: number) {
  const call = fetchMock.mock.calls[index] as [unknown, { headers?: HeadersInit } | undefined];
  return (call[1]?.headers ?? {}) as Record<string, string>;
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

  it('does not grant workspace-admin affordances from the legacy localhost dev-header flag', () => {
    window.localStorage.setItem('naruon_dev_user', 'admin');
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('http://localhost/settings'),
    });

    const client = new ApiClient('');

    expect(client.canManageWorkspaceSettings()).toBe(false);

    client.setDevHeaderAuthEnabled(true);
    expect(client.canManageWorkspaceSettings()).toBe(false);

    client.setDevHeaderAuthEnabled(false);
    expect(client.canManageWorkspaceSettings()).toBe(false);
  });

  it('reports localhost workspace access ready after runtime config but keeps dev-header admins denied', async () => {
    window.localStorage.setItem('naruon_dev_user', 'admin');
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('http://localhost/prompt-studio'),
    });
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        features: {
          dev_header_auth_enabled: true,
        },
      }),
    }));
    vi.stubGlobal('fetch', fetchMock);

    const client = new ApiClient('');

    expect(client.isWorkspaceSettingsAccessReady()).toBe(false);
    expect(client.canManageWorkspaceSettings()).toBe(false);

    await client.ensureWorkspaceSettingsAccessReady();

    expect(client.isWorkspaceSettingsAccessReady()).toBe(true);
    expect(client.canManageWorkspaceSettings()).toBe(false);
    expect(fetchMock).toHaveBeenCalledWith('/api/runtime-config', {
      headers: { 'Content-Type': 'application/json' },
    });
  });

  it('allows bearer-scoped workspace admins without relying on dev-header auth', () => {
    window.localStorage.setItem('naruon_bearer_token', createUnsignedToken({
      sub: 'admin-1',
      roles: ['organization_admin'],
      organization_id: 'org-acme',
      exp: Math.floor(Date.now() / 1000) + 60,
    }));
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('https://app.example.com/settings'),
    });

    const client = new ApiClient('');

    expect(client.canManageWorkspaceSettings()).toBe(true);
  });

  it('does not fall back to localhost organization scope for bearer admin claims without org scope', () => {
    window.localStorage.setItem('naruon_bearer_token', createUnsignedToken({
      sub: 'admin-1',
      roles: ['organization_admin'],
      exp: Math.floor(Date.now() / 1000) + 60,
    }));
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: new URL('http://localhost/prompt-studio'),
    });

    const client = new ApiClient('');

    expect(client.canManageWorkspaceSettings()).toBe(false);
  });

  it('does not treat group admins as workspace settings admins', () => {
    window.localStorage.setItem('naruon_bearer_token', createUnsignedToken({
      sub: 'group-admin-1',
      roles: ['group_admin'],
      organization_id: 'org-acme',
      exp: Math.floor(Date.now() / 1000) + 60,
    }));

    const client = new ApiClient('');

    expect(client.canManageWorkspaceSettings()).toBe(false);
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

    const headers = headersForCall(fetchMock, 0);
    expect(headers['X-User-Id']).toBeUndefined();
    expect(headers['X-User-Role']).toBeUndefined();
    expect(headers['X-Organization-Id']).toBeUndefined();
  });

  it('does not send scoped dev headers even if runtime config enables the legacy flag', async () => {
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

    const runtimeHeaders = headersForCall(fetchMock, 0);
    const apiHeaders = headersForCall(fetchMock, 1);
    expect(runtimeHeaders['X-User-Id']).toBeUndefined();
    expect(apiHeaders['X-User-Id']).toBeUndefined();
    expect(apiHeaders['X-User-Role']).toBeUndefined();
    expect(apiHeaders['X-Organization-Id']).toBeUndefined();
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

    const apiHeaders = headersForCall(fetchMock, 1);
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
    const headers = headersForCall(fetchMock, 0);
    expect(headers.Authorization).toBeUndefined();
    expect(headers['X-User-Id']).toBeUndefined();
  });
});
