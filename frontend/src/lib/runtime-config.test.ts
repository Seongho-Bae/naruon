/* @vitest-environment jsdom */
import { afterEach, describe, expect, it, vi } from 'vitest';

import { getRuntimeConfig, resetRuntimeConfigCache } from './runtime-config';

function jsonResponse(body: unknown) {
  return {
    ok: true,
    json: async () => body,
  };
}

describe('runtime config helpers', () => {
  afterEach(() => {
    resetRuntimeConfigCache();
    vi.unstubAllGlobals();
  });

  it('reads auth capability flags so the frontend can hide unsupported manual bearer login', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({
      product_name: 'Naruon',
      version: '0.5.1',
      features: {
        llm_enabled: true,
        smtp_enabled: true,
        imap_enabled: true,
        dev_header_auth_enabled: true,
        manual_bearer_login_enabled: false,
      },
    })));

    const config = await getRuntimeConfig();

    expect(config.features.dev_header_auth_enabled).toBe(true);
    expect(config.features.manual_bearer_login_enabled).toBe(false);
  });
});
