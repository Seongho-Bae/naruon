/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/avatar", () => ({
  Avatar: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AvatarFallback: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/components/ui/input", () => ({
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
}));

vi.mock("lucide-react", () => ({
  Inbox: () => <svg aria-hidden="true" />,
  Mail: () => <svg aria-hidden="true" />,
  MessagesSquare: () => <svg aria-hidden="true" />,
  Paperclip: () => <svg aria-hidden="true" />,
  RefreshCw: () => <svg aria-hidden="true" />,
  Search: () => <svg aria-hidden="true" />,
  Sparkles: () => <svg aria-hidden="true" />,
  Star: () => <svg aria-hidden="true" />,
}));

import { EmailList, validateSearchQuery } from "./EmailList";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

function jsonResponse(body: unknown) {
  return {
    ok: true,
    json: async () => body,
  };
}

async function flushAsyncWork() {
  for (let index = 0; index < 5; index += 1) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

async function renderEmailList(fetchMock: ReturnType<typeof vi.fn>) {
  vi.stubGlobal("fetch", fetchMock);
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);

  await act(async () => {
    root.render(<EmailList onSelectEmail={() => undefined} />);
  });
  await flushAsyncWork();

  return { container, root };
}

describe("EmailList", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) {
      act(() => root?.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    vi.unstubAllGlobals();
  });

  it("normalizes search text before sending it to the search API", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/emails")) return Promise.resolve(jsonResponse({ emails: [] }));
      if (url.endsWith("/api/search")) return Promise.resolve(jsonResponse({ results: [] }));
      throw new Error(`Unexpected fetch: ${url}`);
    });
    ({ container, root } = await renderEmailList(fetchMock));

    const input = container.querySelector<HTMLInputElement>("#email-search");
    const form = container.querySelector<HTMLFormElement>("form");
    expect(input).not.toBeNull();
    expect(form).not.toBeNull();

    await act(async () => {
      input!.value = "  quarterly\n   roadmap\t  ";
      input!.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => {
      form!.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    });
    await flushAsyncWork();

    const searchCall = fetchMock.mock.calls.find(([inputArg]) => String(inputArg).endsWith("/api/search"));
    expect(searchCall).toBeDefined();
    const searchOptions = (searchCall as unknown as [RequestInfo | URL, RequestInit] | undefined)?.[1];
    expect(JSON.parse(String(searchOptions?.body))).toEqual({ query: "quarterly roadmap" });
  });

  it("rejects unsafe control characters during search validation", () => {
    expect(validateSearchQuery("invoice\u0000 OR 1=1")).toEqual({
      query: "",
      error: "검색어에 사용할 수 없는 문자가 포함되어 있습니다.",
    });
  });

  it("rejects overlong search text during search validation", () => {
    expect(validateSearchQuery("a".repeat(513))).toEqual({
      query: "",
      error: "검색어는 512자 이하로 입력하세요.",
    });
  });
});
