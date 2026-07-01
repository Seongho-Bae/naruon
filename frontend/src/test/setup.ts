globalThis.IS_REACT_ACT_ENVIRONMENT = true;

if (typeof window !== "undefined") {
  const createMemoryStorage = () => {
    const entries = new Map<string, string>();
    return {
      get length() {
        return entries.size;
      },
      clear() {
        entries.clear();
      },
      getItem(key: string) {
        return entries.get(key) ?? null;
      },
      key(index: number) {
        return Array.from(entries.keys())[index] ?? null;
      },
      removeItem(key: string) {
        entries.delete(key);
      },
      setItem(key: string, value: string) {
        entries.set(key, String(value));
      },
    } satisfies Storage;
  };

  const descriptor = Object.getOwnPropertyDescriptor(window, "localStorage");
  const storage =
    descriptor && "value" in descriptor && descriptor.value
      ? (descriptor.value as Storage)
      : createMemoryStorage();

  if (!descriptor || descriptor.configurable) {
    try {
      Object.defineProperty(window, "localStorage", {
        configurable: true,
        value: storage,
      });
    } catch {
      // Some jsdom/browser implementations expose a non-configurable localStorage.
    }
  }

  try {
    Object.defineProperty(globalThis, "localStorage", {
      configurable: true,
      value: storage,
    });
  } catch {
    // Keep tests running even if the host provides a locked global storage.
  }
}
