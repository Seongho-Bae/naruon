/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EmailList } from "./EmailList";

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

  it("renders the branded dense inbox and selected thread state", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(
        jsonResponse({
          emails: [
            {
              id: 7,
              sender: "김지현 PM",
              subject: null,
              date: "2026-05-11T09:30:00Z",
              snippet: "Q2 출시 계획과 우선순위 조정 요청입니다.",
              unread: true,
              reply_count: 3,
            },
          ],
        }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<EmailList onSelectEmail={vi.fn()} selectedEmailId={7} />);
    });
    await flushAsyncWork();

    const selectedThread = container.querySelector('button[aria-current="true"]');

    expect(fetchMock).toHaveBeenCalledWith("/api/emails", expect.any(Object));
    expect(container.textContent).toContain("받은편지함");
    expect(container.textContent).toContain("맥락 종합");
    expect(container.textContent).toContain("실행 항목");
    expect(container.textContent).toContain("(제목 없음)");
    expect(container.textContent).toContain("새 메일");
    expect(container.textContent).toContain("3개 메시지");
    expect(selectedThread).not.toBeNull();
    expect(selectedThread?.className).toContain("min-h-20");
  });
});
