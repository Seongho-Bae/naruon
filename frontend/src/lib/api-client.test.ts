import { afterEach, describe, expect, it } from 'vitest';

import { buildApiHeaders } from './api-client';

const ORIGINAL_TOKEN = process.env.NEXT_PUBLIC_API_AUTH_TOKEN;

afterEach(() => {
  process.env.NEXT_PUBLIC_API_AUTH_TOKEN = ORIGINAL_TOKEN;
});

describe('buildApiHeaders', () => {
  it('adds the local bearer token when a public development token is configured', () => {
    process.env.NEXT_PUBLIC_API_AUTH_TOKEN = 'local-dev-token';

    const headers = buildApiHeaders({ 'Content-Type': 'application/json' });

    expect(headers.get('Authorization')).toBe('Bearer local-dev-token');
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  it('does not overwrite an explicit authorization header', () => {
    process.env.NEXT_PUBLIC_API_AUTH_TOKEN = 'local-dev-token';

    const headers = buildApiHeaders({ Authorization: 'Bearer session-token' });

    expect(headers.get('Authorization')).toBe('Bearer session-token');
  });
});
