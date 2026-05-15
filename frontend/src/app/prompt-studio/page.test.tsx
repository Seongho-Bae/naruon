/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

const apiClientMock = vi.hoisted(() => ({
  canManageWorkspaceSettings: vi.fn(() => false),
  isWorkspaceSettingsAccessReady: vi.fn(() => true),
  ensureWorkspaceSettingsAccessReady: vi.fn(async () => {}),
  post: vi.fn(),
}));

vi.mock("@/lib/api-client", () => ({
  apiClient: apiClientMock,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
}));

vi.mock("@/components/ui/input", () => ({
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
}));

vi.mock("@/components/ui/textarea", () => ({
  Textarea: (props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) => <textarea {...props} />,
}));

vi.mock("@/components/ui/checkbox", () => ({
  Checkbox: ({ checked, onCheckedChange, ...props }: { checked?: boolean; onCheckedChange?: (checked: boolean) => void } & React.InputHTMLAttributes<HTMLInputElement>) => (
    <input
      {...props}
      type="checkbox"
      checked={Boolean(checked)}
      onChange={(event) => onCheckedChange?.(event.currentTarget.checked)}
    />
  ),
}));

vi.mock("lucide-react", () => ({
  Code: () => <svg aria-hidden="true" />,
  Play: () => <svg aria-hidden="true" />,
  Save: () => <svg aria-hidden="true" />,
}));

import PromptStudioPage from "./page";

describe("PromptStudioPage", () => {
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
    apiClientMock.canManageWorkspaceSettings.mockReturnValue(false);
    apiClientMock.isWorkspaceSettingsAccessReady.mockReturnValue(true);
    apiClientMock.ensureWorkspaceSettingsAccessReady.mockResolvedValue(undefined);
  });

  it("blocks member access before any prompt test or save controls render", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<PromptStudioPage />);
    });

    expect(container.textContent).toContain("관리자 권한이 필요합니다");
    expect(container.textContent).not.toContain("실행 (Test)");
    expect(container.textContent).not.toContain("프롬프트 저장 (Save)");
    expect(apiClientMock.post).not.toHaveBeenCalled();
  });

  it("renders prompt test and save controls for workspace admins", () => {
    apiClientMock.canManageWorkspaceSettings.mockReturnValue(true);
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<PromptStudioPage />);
    });

    expect(container.textContent).toContain("Prompt Studio");
    expect(container.textContent).toContain("실행 (Test)");
    expect(container.textContent).toContain("프롬프트 저장 (Save)");
  });

  it("waits for async auth context readiness before denying direct-route access", async () => {
    let resolveReadiness: (() => void) | undefined;
    apiClientMock.isWorkspaceSettingsAccessReady
      .mockReturnValueOnce(false)
      .mockReturnValue(true);
    apiClientMock.ensureWorkspaceSettingsAccessReady.mockImplementation(
      () => new Promise<void>((resolve) => {
        resolveReadiness = resolve;
      }),
    );
    apiClientMock.canManageWorkspaceSettings.mockReturnValue(false);
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<PromptStudioPage />);
    });

    expect(container.textContent).toContain("권한을 확인하고 있습니다");
    expect(container.textContent).not.toContain("관리자 권한이 필요합니다");
    expect(container.textContent).not.toContain("실행 (Test)");

    apiClientMock.canManageWorkspaceSettings.mockReturnValue(true);
    await act(async () => {
      resolveReadiness?.();
      await Promise.resolve();
    });

    expect(container.textContent).toContain("실행 (Test)");
    expect(container.textContent).toContain("프롬프트 저장 (Save)");
    expect(container.textContent).not.toContain("관리자 권한이 필요합니다");
  });
});
