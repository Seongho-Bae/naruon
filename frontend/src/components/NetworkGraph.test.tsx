/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("vis-network", () => ({
  Network: vi.fn(function MockNetwork() {
    return { destroy: vi.fn() };
  }),
}));

import { Network } from "vis-network";

import NetworkGraph from "./NetworkGraph";

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

describe("NetworkGraph", () => {
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
    vi.clearAllMocks();
  });

  it("coerces graph tooltip titles to text-only DOM nodes before vis-network renders them", async () => {
    const maliciousTitle = '<img src=x onerror="globalThis.__xss = true">';
    const fetchMock = vi.fn(() =>
      Promise.resolve(
        jsonResponse({
          nodes: [{ id: "n1", label: "Node", title: maliciousTitle }],
          edges: [{ from: "n1", to: "n1", title: maliciousTitle }],
        }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root?.render(<NetworkGraph />);
    });
    await flushAsyncWork();

    expect(Network).toHaveBeenCalledTimes(1);
    const networkData = vi.mocked(Network).mock.calls[0]?.[1];
    const nodes = Array.isArray(networkData?.nodes) ? networkData.nodes : [];
    const edges = Array.isArray(networkData?.edges) ? networkData.edges : [];
    const nodeTitle = nodes[0]?.title;
    const edgeTitle = edges[0]?.title;

    expect(nodeTitle).toBeInstanceOf(HTMLElement);
    expect(edgeTitle).toBeInstanceOf(HTMLElement);
    expect((nodeTitle as HTMLElement).textContent).toBe(maliciousTitle);
    expect((edgeTitle as HTMLElement).textContent).toBe(maliciousTitle);
    expect((nodeTitle as HTMLElement).innerHTML).not.toContain("<img");
    expect((edgeTitle as HTMLElement).innerHTML).not.toContain("<img");
  });
});
