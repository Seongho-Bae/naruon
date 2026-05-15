/* @vitest-environment jsdom */
import React from 'react';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
}));

import ComposePage from './compose/page';
import { ComposePageClient } from './compose/ComposePageClient';
import StarredPage from './starred/page';
import SentPage from './sent/page';
import DraftsPage from './drafts/page';
import AllMailPage from './all/page';
import ProjectsPage from './projects/page';
import LabelsPage from './labels/page';

describe('app route contract', () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    root?.unmount();
    root = null;
    container?.remove();
    container = null;
  });

  it('exports concrete page modules for primary sidebar destinations and compose flow', async () => {
    expect(typeof ComposePage).toBe('function');
    expect(typeof StarredPage).toBe('function');
    expect(typeof SentPage).toBe('function');
    expect(typeof DraftsPage).toBe('function');
    expect(typeof AllMailPage).toBe('function');
    expect(typeof ProjectsPage).toBe('function');
    expect(typeof LabelsPage).toBe('function');
  });

  it('renders honest placeholder content for 아직 미구현된 mailbox/project/label routes', async () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    const projectsIndex = await ProjectsPage();
    const projectElement = await ProjectsPage({ searchParams: Promise.resolve({ workspace: 'launch' }) });
    const labelsIndex = await LabelsPage();
    const labelElement = await LabelsPage({ searchParams: Promise.resolve({ label: 'urgent' }) });

    act(() => {
      root?.render(
        <div>
          <ComposePageClient />
          <StarredPage />
          <SentPage />
          <DraftsPage />
          <AllMailPage />
          {projectsIndex}
          {projectElement}
          {labelsIndex}
          {labelElement}
        </div>,
      );
    });

    expect(container.textContent).toContain('메일 작성');
    expect(container.textContent).toContain('중요 메일 보드 준비 중');
    expect(container.textContent).toContain('보낸 메일 보드 준비 중');
    expect(container.textContent).toContain('임시 보관함 보드 준비 중');
    expect(container.textContent).toContain('전체 메일 보드 준비 중');
    expect(container.textContent).toContain('프로젝트 모음 준비 중');
    expect(container.textContent).toContain('런칭 프로젝트 워크스페이스 준비 중');
    expect(container.textContent).toContain('라벨 모음 준비 중');
    expect(container.textContent).toContain('긴급 라벨 워크스페이스 준비 중');
  });
});
