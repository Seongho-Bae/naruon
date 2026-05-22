/* @vitest-environment jsdom */
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';

import { toSafeReactText } from './safe-text';

describe('toSafeReactText', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
  });

  it('keeps readable email text on React text-node rendering path', () => {
    expect(toSafeReactText('AT&T: 2 < 3 and Tom "T"')).toBe('AT&T: 2 < 3 and Tom "T"');
  });

  it('renders dangerous-looking markup as text instead of HTML', () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    const unsafeText = `<img src=x onerror="alert('xss')">`;

    act(() => {
      root?.render(<div>{toSafeReactText(unsafeText)}</div>);
    });

    expect(container.textContent).toBe(unsafeText);
    expect(container.querySelector('img')).toBeNull();
    expect(container.innerHTML).toContain('&lt;img');
  });

  it('replaces ambiguous control characters before display', () => {
    expect(toSafeReactText('hello\u0000world')).toBe('hello\uFFFDworld');
  });
});
