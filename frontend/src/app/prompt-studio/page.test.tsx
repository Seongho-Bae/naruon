/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

const apiMocks = vi.hoisted(() => ({
  post: vi.fn(),
}));

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    post: apiMocks.post,
  },
}));

vi.mock("lucide-react", () => ({
  CheckIcon: () => <svg aria-hidden="true" />,
  Code: () => <svg aria-hidden="true" />,
  Loader2: () => <svg aria-hidden="true" data-testid="loader" />,
  Play: () => <svg aria-hidden="true" />,
  Save: () => <svg aria-hidden="true" />,
}));

import PromptStudioPage from "./page";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, reject, resolve };
}

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

function getButton(container: HTMLElement, label: string) {
  const button = Array.from(container.querySelectorAll("button")).find((node) =>
    node.textContent?.includes(label),
  );
  expect(button).toBeInstanceOf(HTMLButtonElement);
  return button as HTMLButtonElement;
}

describe("PromptStudioPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  async function renderPage() {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<PromptStudioPage />);
    });
    return container;
  }

  it("associates labels with editable prompt fields", async () => {
    const page = await renderPage();

    for (const fieldId of [
      "prompt-title",
      "prompt-description",
      "prompt-content",
      "test-variable",
      "is_shared",
    ]) {
      expect(page.querySelector(`#${fieldId}`)).not.toBeNull();
      expect(page.querySelector(`label[for="${fieldId}"]`)).not.toBeNull();
    }
  });

  it("shows disabled loading feedback while testing a prompt", async () => {
    const promptTest = deferred<{ result: string }>();
    apiMocks.post.mockReturnValueOnce(promptTest.promise);
    const page = await renderPage();

    act(() => {
      getButton(page, "실행 (Test)").click();
    });

    expect(getButton(page, "테스트 중...").disabled).toBe(true);
    expect(page.querySelector("[data-testid='loader']")).not.toBeNull();

    await act(async () => {
      promptTest.resolve({ result: "요약 결과" });
      await promptTest.promise;
    });
    await flushAsyncWork();

    expect(getButton(page, "실행 (Test)").disabled).toBe(false);
    expect(page.textContent).toContain("요약 결과");
    expect(apiMocks.post).toHaveBeenCalledWith("/api/prompts/test", {
      content: "핵심 맥락을 종합해주세요: {{email}}",
      variables: { email: "메일 내용 예시입니다." },
    });
  });

  it("shows disabled loading feedback while saving a prompt", async () => {
    const promptSave = deferred<{ result?: string }>();
    apiMocks.post.mockReturnValueOnce(promptSave.promise);
    vi.stubGlobal("alert", vi.fn());
    const page = await renderPage();

    act(() => {
      getButton(page, "프롬프트 저장 (Save)").click();
    });

    expect(getButton(page, "저장 중...").disabled).toBe(true);
    expect(page.querySelector("[data-testid='loader']")).not.toBeNull();

    await act(async () => {
      promptSave.resolve({});
      await promptSave.promise;
    });
    await flushAsyncWork();

    expect(getButton(page, "프롬프트 저장 (Save)").disabled).toBe(false);
    expect(apiMocks.post).toHaveBeenCalledWith("/api/prompts", {
      title: "",
      description: "",
      content: "핵심 맥락을 종합해주세요: {{email}}",
      is_shared: false,
    });
  });
});
