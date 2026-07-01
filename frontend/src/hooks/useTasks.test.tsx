/* @vitest-environment jsdom */
import React, { act, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useTasks, type TaskItem } from "./useTasks";

const doneTask: TaskItem = {
  id: "task-done",
  title: "계약 승인 확인",
  status: "done",
  priority: "high",
  created_at: "2026-05-17T09:00:00Z",
  updated_at: "2026-05-17T10:00:00Z",
};

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

async function waitForCondition(condition: () => boolean) {
  for (let index = 0; index < 20; index += 1) {
    if (condition()) return;
    await flushAsyncWork();
  }
  throw new Error("waitForCondition timed out after 20 attempts");
}

function HookHarness() {
  const [tasks, setTasks] = useState<TaskItem[]>([doneTask]);
  const {
    taskUpdateStatusById,
    handleTaskCompletionToggle,
  } = useTasks(setTasks, (title, fallback = "제목 없는 작업") => title?.trim() || fallback);
  const task = tasks[0];

  return (
    <section>
      <button type="button" onClick={() => void handleTaskCompletionToggle(task)}>
        {task.status}
      </button>
      {Array.from(taskUpdateStatusById.entries()).map(([taskId, message]) => (
        <p key={taskId} role="status">{message}</p>
      ))}
    </section>
  );
}

describe("useTasks", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    const mountedRoot = root;
    if (mountedRoot) {
      act(() => mountedRoot.unmount());
    }
    root = null;
    container?.remove();
    container = null;
    vi.unstubAllGlobals();
  });

  it("reports reopened feedback when toggling a completed task back to open", async () => {
    const fetchCalls: Array<{ url: string; init?: RequestInit }> = [];
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      fetchCalls.push({ url, init });
      if (url.endsWith("/api/tasks/task-done")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ ...doneTask, status: "open", updated_at: "2026-05-17T11:00:00Z" }),
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    }));
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<HookHarness />);
    });

    const toggleButton = container.querySelector<HTMLButtonElement>("button");
    expect(toggleButton?.textContent).toBe("done");

    await act(async () => {
      toggleButton?.click();
    });
    await waitForCondition(() => container?.textContent?.includes("계약 승인 확인 작업을 다시 열었습니다.") ?? false);

    const patchCall = fetchCalls.find((call) => call.url.endsWith("/api/tasks/task-done"));
    expect(patchCall?.init?.method).toBe("PATCH");
    expect(JSON.parse(String(patchCall?.init?.body))).toEqual({ status: "open" });
    expect(container.textContent).toContain("open");
  });
});
