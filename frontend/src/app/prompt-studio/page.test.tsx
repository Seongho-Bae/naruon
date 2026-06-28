/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

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

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function signedSessionResponse() {
  return jsonResponse({
    claims: {
      userId: "user-1",
      organizationId: "org-1",
      workspaceId: "workspace-1",
    },
  });
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

function lowerCaseHeaders(headers: HeadersInit | undefined) {
  if (!headers) return {};
  if (headers instanceof Headers) {
    return Object.fromEntries(
      Array.from(headers.entries()).map(([key, value]) => [
        key.toLowerCase(),
        value,
      ]),
    );
  }
  if (Array.isArray(headers)) {
    return Object.fromEntries(
      headers.map(([key, value]) => [key.toLowerCase(), value]),
    );
  }
  return Object.fromEntries(
    Object.entries(headers).map(([key, value]) => [key.toLowerCase(), value]),
  );
}

function expectNoPublicIdentityHeaders(headers: HeadersInit | undefined) {
  const lowerHeaders = lowerCaseHeaders(headers);
  expect(lowerHeaders.authorization).toBeUndefined();
  for (const headerName of [
    "x-user-id",
    "x-organization-id",
    "x-group-id",
    "x-group-ids",
    "x-user-role",
    "x-dev-auth-token",
  ]) {
    expect(lowerHeaders[headerName]).toBeUndefined();
  }
}

function findFetchCall(fetchMock: ReturnType<typeof vi.fn>, endpoint: string) {
  const call = fetchMock.mock.calls.find(([input]) => String(input) === endpoint);
  expect(call).toBeDefined();
  return call as [RequestInfo | URL, RequestInit?];
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
    const promptTest = deferred<Response>();
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/auth/session") return Promise.resolve(signedSessionResponse());
      if (url === "/api/prompts/test") return promptTest.promise;
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const page = await renderPage();

    act(() => {
      getButton(page, "실행 (Test)").click();
    });

    expect(getButton(page, "테스트 중...").disabled).toBe(true);
    expect(getButton(page, "테스트 중...").getAttribute("aria-busy")).toBe("true");
    expect(page.querySelector("[data-testid='loader']")).not.toBeNull();

    await act(async () => {
      promptTest.resolve(jsonResponse({ result: "맥락 종합 결과" }));
      await promptTest.promise;
    });
    await flushAsyncWork();

    expect(getButton(page, "실행 (Test)").disabled).toBe(false);
    expect(getButton(page, "실행 (Test)").getAttribute("aria-busy")).toBe("false");
    expect(page.textContent).toContain("맥락 종합 결과");
    const sessionCall = findFetchCall(fetchMock, "/auth/session");
    expect(sessionCall[1]).toEqual(expect.objectContaining({ credentials: "same-origin", method: "GET" }));

    const promptCall = findFetchCall(fetchMock, "/api/prompts/test");
    expect(promptCall[1]).toEqual(expect.objectContaining({
      body: JSON.stringify({
        content: "핵심 맥락을 종합해주세요: {{email}}",
        variables: { email: "메일 내용 예시입니다." },
      }),
      credentials: "same-origin",
      method: "POST",
    }));
    expectNoPublicIdentityHeaders(promptCall[1]?.headers);
  });

  it("shows disabled loading feedback while saving a prompt", async () => {
    const promptSave = deferred<Response>();
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/auth/session") return Promise.resolve(signedSessionResponse());
      if (url === "/api/prompts") return promptSave.promise;
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("alert", vi.fn());
    const page = await renderPage();

    act(() => {
      getButton(page, "프롬프트 저장 (Save)").click();
    });

    expect(getButton(page, "저장 중...").disabled).toBe(true);
    expect(getButton(page, "저장 중...").getAttribute("aria-busy")).toBe("true");
    expect(page.querySelector("[data-testid='loader']")).not.toBeNull();

    await act(async () => {
      promptSave.resolve(jsonResponse({}));
      await promptSave.promise;
    });
    await flushAsyncWork();

    expect(getButton(page, "프롬프트 저장 (Save)").disabled).toBe(false);
    expect(getButton(page, "프롬프트 저장 (Save)").getAttribute("aria-busy")).toBe("false");
    const sessionCall = findFetchCall(fetchMock, "/auth/session");
    expect(sessionCall[1]).toEqual(expect.objectContaining({ credentials: "same-origin", method: "GET" }));

    const promptCall = findFetchCall(fetchMock, "/api/prompts");
    expect(promptCall[1]).toEqual(expect.objectContaining({
      body: JSON.stringify({
        title: "",
        description: "",
        content: "핵심 맥락을 종합해주세요: {{email}}",
        is_shared: false,
      }),
      credentials: "same-origin",
      method: "POST",
    }));
    expectNoPublicIdentityHeaders(promptCall[1]?.headers);
  });

  it("blocks prompt operations before calling prompt APIs without a signed session", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/auth/session") return Promise.resolve(jsonResponse({ claims: {} }));
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const page = await renderPage();

    act(() => {
      getButton(page, "실행 (Test)").click();
    });
    await flushAsyncWork();

    expect(page.textContent).toContain("서명된 사용자 세션");
    expect(fetchMock.mock.calls.map(([input]) => String(input))).toEqual(["/auth/session"]);
  });
});
