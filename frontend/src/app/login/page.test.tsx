/* @vitest-environment jsdom */
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';

const apiClientMock = vi.hoisted(() => ({
  canUseManualBearerSession: vi.fn(),
  getSessionClaims: vi.fn(),
  setBearerToken: vi.fn(),
  clearBearerToken: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: apiClientMock,
}));

const getRuntimeConfigMock = vi.hoisted(() => vi.fn());

vi.mock('@/lib/runtime-config', () => ({
  getRuntimeConfig: getRuntimeConfigMock,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
}));

vi.mock('lucide-react', () => {
  const Icon = () => <svg aria-hidden="true" />;
  return {
    KeyRound: Icon,
    ShieldCheck: Icon,
    LogOut: Icon,
  };
});

import LoginPage from './page';

describe('LoginPage', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    vi.clearAllMocks();
  });

  it('blocks manual bearer token entry outside explicit local environments', async () => {
    apiClientMock.canUseManualBearerSession.mockReturnValue(false);
    apiClientMock.getSessionClaims.mockReturnValue(null);
    getRuntimeConfigMock.mockResolvedValue({
      features: {
        dev_header_auth_enabled: true,
        manual_bearer_login_enabled: false,
      },
    });

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<LoginPage />);
    });
    await act(async () => {
      await Promise.resolve();
    });

    expect(container.textContent).toContain('로그인 / 세션');
    expect(container.textContent).toContain('trusted header 인증');
    expect(container.textContent).not.toContain('토큰 저장');
  });
});
