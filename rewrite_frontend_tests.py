# 4. Update frontend tests
with open("frontend/src/components/EmailDetail.test.tsx", "r") as f:
    content = f.read()

if "translates email content when the Translate button is clicked" not in content:
    test_code = """
  it("translates email content when the Translate button is clicked", async () => {
    let translateResolver: (value: Response) => void;
    const translatePromise = new Promise<Response>((resolve) => {
      translateResolver = resolve;
    });

    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith("/api/emails/1")) {
        return jsonResponse({
          id: 1,
          subject: "Test Subject",
          sender: "test@example.com",
          body: "Hello World",
          received_at: "2026-05-18T10:00:00Z",
          thread_id: "thread-1"
        });
      }
      if (url.endsWith("/api/emails/thread-1")) {
        return jsonResponse([{ id: 1 }]);
      }
      if (url.endsWith("/api/llm/summarize")) {
        return jsonResponse({ summary: "Summary", todos: [] });
      }
      if (url.endsWith("/api/llm/translate")) {
        return translatePromise;
      }
      return jsonResponse({});
    }));

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    await act(async () => { root?.render(<EmailDetail emailId={1} />); });
    await flushAsyncWork();

    const translateButton = Array.from(container?.querySelectorAll('button') || []).find(b => b.textContent?.includes('번역'));
    expect(translateButton).toBeDefined();

    act(() => { translateButton?.click(); });

    await act(async () => {
      translateResolver(jsonResponse({ translation: "안녕하세요 세계" }));
      await translatePromise;
    });
    await flushAsyncWork();
  });

  it("handles translation errors gracefully", async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith("/api/emails/1")) {
        return jsonResponse({
          id: 1,
          subject: "Test Subject",
          sender: "test@example.com",
          body: "Hello World",
          received_at: "2026-05-18T10:00:00Z",
          thread_id: "thread-1"
        });
      }
      if (url.endsWith("/api/emails/thread-1")) {
        return jsonResponse([{ id: 1 }]);
      }
      if (url.endsWith("/api/llm/summarize")) {
        return jsonResponse({ summary: "Summary", todos: [] });
      }
      if (url.endsWith("/api/llm/translate")) {
        return new Response("Internal Server Error", { status: 500 });
      }
      return jsonResponse({});
    }));

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    await act(async () => { root?.render(<EmailDetail emailId={1} />); });
    await flushAsyncWork();

    const translateButton = Array.from(container?.querySelectorAll('button') || []).find(b => b.textContent?.includes('번역'));

    act(() => { translateButton?.click(); });
    await flushAsyncWork();
  });
"""
    content = content.replace("describe(\"EmailDetail\", () => {", "describe(\"EmailDetail\", () => {\n" + test_code)
    with open("frontend/src/components/EmailDetail.test.tsx", "w") as f:
        f.write(content)
