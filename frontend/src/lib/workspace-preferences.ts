import { useSyncExternalStore } from 'react';

export type WorkspaceStartupView = 'dashboard' | 'email' | 'calendar';

const STARTUP_VIEW_KEY = 'naruon_startup_view';
const DEFAULT_STARTUP_VIEW: WorkspaceStartupView = 'dashboard';

function isWorkspaceStartupView(value: string | null): value is WorkspaceStartupView {
  return value === 'dashboard' || value === 'email' || value === 'calendar';
}

export function getWorkspaceStartupView(): WorkspaceStartupView {
  if (typeof window === 'undefined') {
    return DEFAULT_STARTUP_VIEW;
  }

  try {
    const stored = window.localStorage.getItem(STARTUP_VIEW_KEY);
    return isWorkspaceStartupView(stored) ? stored : DEFAULT_STARTUP_VIEW;
  } catch {
    return DEFAULT_STARTUP_VIEW;
  }
}

export function setWorkspaceStartupView(view: WorkspaceStartupView) {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.localStorage.setItem(STARTUP_VIEW_KEY, view);
  } catch {
    // Restricted/private browsing can reject localStorage writes; keep the UI responsive.
  }
  window.dispatchEvent(new CustomEvent('naruon:startup-view-change', { detail: { view } }));
}

export function subscribeWorkspaceStartupView(listener: () => void) {
  if (typeof window === 'undefined') {
    return () => undefined;
  }

  const handleStorage = (event: StorageEvent) => {
    if (event.key === STARTUP_VIEW_KEY) {
      listener();
    }
  };
  window.addEventListener('naruon:startup-view-change', listener);
  window.addEventListener('storage', handleStorage);
  return () => {
    window.removeEventListener('naruon:startup-view-change', listener);
    window.removeEventListener('storage', handleStorage);
  };
}

export function useWorkspaceStartupView() {
  return useSyncExternalStore(
    subscribeWorkspaceStartupView,
    getWorkspaceStartupView,
    () => DEFAULT_STARTUP_VIEW,
  );
}
