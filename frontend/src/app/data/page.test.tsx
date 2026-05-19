/* @vitest-environment jsdom */
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("lucide-react", () => ({
  Database: () => <svg aria-hidden="true" />,
  FileArchive: () => <svg aria-hidden="true" />,
  FolderTree: () => <svg aria-hidden="true" />,
  ShieldCheck: () => <svg aria-hidden="true" />,
}));

import DataPage from "./page";

describe("DataPage", () => {
  let root: Root | null = null;
  let container: HTMLDivElement | null = null;

  afterEach(() => {
    if (root) act(() => root?.unmount());
    root = null;
    container?.remove();
    container = null;
  });

  it("renders document repository ingestion embeddings quality and WebDAV writeback details", () => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    act(() => {
      root?.render(<DataPage />);
    });

    expect(container.querySelector("h1")?.textContent).toContain("데이터와 파일");
    expect(container.textContent).toContain("문서 저장소");
    expect(container.textContent).toContain("수집 파이프라인");
    expect(container.textContent).toContain("임베딩");
    expect(container.textContent).toContain("품질 점검");
    expect(container.textContent).toContain("WebDAV writeback 큐");
    expect(container.textContent).toContain("중복 반입");
    expect(container.textContent).toContain("unique email");
  });
});
