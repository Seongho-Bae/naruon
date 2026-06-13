import { expect, test } from '@playwright/test';
import crypto from 'node:crypto';

const liveSessionPayload = {
  ver: 1,
  iss: 'naruon-control-plane',
  aud: 'naruon-api',
  sub: 'testuser',
  role: 'member',
  org: 'org-acme',
  groups: ['group-1', 'group-2'],
  workspace: 'workspace-org-acme',
};

function encodeJson(value: unknown): string {
  return Buffer.from(JSON.stringify(value)).toString('base64url');
}

function signLiveSession(): string {
  const secret = process.env.LIVE_E2E_SESSION_SECRET;
  if (!secret) {
    throw new Error('LIVE_E2E_SESSION_SECRET is required for live smoke tests.');
  }

  const header = encodeJson({ alg: 'HS256', typ: 'JWT' });
  const payload = encodeJson({
    ...liveSessionPayload,
    exp: Math.floor(Date.now() / 1000) + 300,
  });
  const signature = crypto
    .createHmac('sha256', secret)
    .update(`${header}.${payload}`, 'ascii')
    .digest('base64url');

  return `${header}.${payload}.${signature}`;
}

async function hasVisibleSeededInboxText(page: import('@playwright/test').Page): Promise<boolean> {
  return page.getByText('Live E2E Release').evaluateAll((elements) =>
    elements.some((element) => {
      const style = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return (
        style.display !== 'none' &&
        style.visibility !== 'hidden' &&
        rect.width > 0 &&
        rect.height > 0
      );
    }),
  );
}

test.skip(
  !process.env.LIVE_BASE_URL && process.env.RUN_LIVE_E2E !== '1',
  'Requires a live frontend/backend environment with seeded data.',
);

test.beforeEach(async ({ page }) => {
  page.on('console', (message) => {
    if (['warning', 'error'].includes(message.type())) {
      throw new Error(`Console ${message.type()}: ${message.text()}`);
    }
  });
  page.on('pageerror', (error) => {
    throw error;
  });
});

test('live dashboard renders seeded inbox through real HTTP', async ({ page }) => {
  const sessionToken = signLiveSession();

  await page.addInitScript((token) => {
    document.cookie = `naruon_session=${token}; Path=/; SameSite=Lax`;
  }, sessionToken);
  await page.goto('/');

  await expect(page.getByRole('img', { name: 'Naruon' })).toBeVisible();
  await expect.poll(() => hasVisibleSeededInboxText(page), {
    timeout: 15_000,
  }).toBe(true);
  await expect(page.getByText('Failed to load emails.')).toHaveCount(0);
});
