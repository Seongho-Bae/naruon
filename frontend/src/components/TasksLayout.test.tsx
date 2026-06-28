/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("lucide-react", () => ({
  Plus: () => <svg aria-hidden="true" />,
  Search: () => <svg aria-hidden="true" />,
  Filter: () => <svg aria-hidden="true" />,
  User: () => <svg aria-hidden="true" />,
  CalendarDays: () => <svg aria-hidden="true" />,
  Inbox: () => <svg aria-hidden="true" />,
  AlertCircle: () => <svg aria-hidden="true" />,
  X: () => <svg aria-hidden="true" />,
}));

import { TasksLayout } from "./TasksLayout";

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
      await new Promise((resolve) => setTimeout(resolve, 10)); // increased timeout for useDeferredValue to settle
    });
  }
}

describe("TasksLayout", () => {
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

  it("renders personal task rows as keyboard-native buttons that open details", async () => {
    const task = {
      id: "task-public-1",
      title: "거래처 회신 준비",
      status: "open",
      priority: "high",
      source_type: "email",
      source_email_id: "mail-public-1",
      related_thread_id: "thread-public-1",
      updated_at: "2026-06-18T05:00:00Z",
    };
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/tasks")) return Promise.resolve(jsonResponse([task]));
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<TasksLayout />);
    });
    await flushAsyncWork();

    const myTasksTab = Array.from(container.querySelectorAll<HTMLButtonElement>("button"))
      .find((button) => button.textContent === "내 작업");

    act(() => {
      myTasksTab?.click();
    });

    const taskButton = Array.from(container.querySelectorAll<HTMLButtonElement>("button"))
      .find((button) => button.textContent?.includes("거래처 회신 준비"));

    expect(taskButton).not.toBeUndefined();
    expect(taskButton?.type).toBe("button");
    expect(taskButton?.className).toContain("focus-visible:ring-ring/40");

    act(() => {
      taskButton?.click();
    });

    expect(container.textContent).toContain("작업 설명");
    expect(container.textContent).toContain("관련 메일 열기");
    expect(container.textContent).toContain("거래처 회신 준비");
  });

  it("keeps untrusted task titles on the React text-node path", async () => {
    const task = {
      id: "task-xss-1",
      title: '<img src=x onerror="alert(document.cookie)"> 긴급 확인',
      status: "open",
      priority: "urgent",
      source_type: "email",
      source_email_id: "mail-xss-1",
      related_thread_id: "thread-xss-1",
      updated_at: "2026-06-18T05:00:00Z",
    };
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/tasks")) return Promise.resolve(jsonResponse([task]));
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<TasksLayout />);
    });
    await flushAsyncWork();

    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("[onerror]")).toBeNull();
    expect(container.textContent).toContain('img src=x onerror="alert(document.cookie)" 긴급 확인');
    expect(container.textContent).not.toContain("<img");
  });

  it("filters tasks using search input and uses deferred value", async () => {
    const tasks = [
      {
        id: "task-1",
        title: "Alpha Task",
        status: "open",
        priority: "normal",
        source_type: "email",
        updated_at: "2026-06-18T05:00:00Z",
      },
      {
        id: "task-2",
        title: "Beta Task",
        status: "in_progress",
        priority: "high",
        source_type: "calendar",
        updated_at: "2026-06-18T06:00:00Z",
      }
    ];

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/tasks")) return Promise.resolve(jsonResponse(tasks));
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<TasksLayout />);
    });
    await flushAsyncWork();

    expect(container.textContent).toContain("Alpha Task");
    expect(container.textContent).toContain("Beta Task");

    const searchInput = container.querySelector<HTMLInputElement>("input[type='search']");
    expect(searchInput).not.toBeNull();

    // Type "Beta"
    await act(async () => {
      if (searchInput) {
        // use fireEvent/dispatchEvent pattern properly for react 19
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype,
          "value"
        )?.set;
        nativeInputValueSetter?.call(searchInput, "Beta");
        searchInput.dispatchEvent(new Event("input", { bubbles: true }));
        // Immediately after typing, before deferred value updates, both tasks
        // should still be visible (deferred filter has not been applied yet)
        expect(container.textContent).toContain("Alpha Task");
        expect(container.textContent).toContain("Beta Task");
      }
    });

    // Defer
    await flushAsyncWork();

    expect(container.textContent).not.toContain("Alpha Task");
    expect(container.textContent).toContain("Beta Task");
  });
});
