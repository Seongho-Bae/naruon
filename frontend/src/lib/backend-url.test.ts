import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { backendApiBaseUrl, parseBackendInternalUrl } from "./backend-url";

const ORIGINAL_ENV = { ...process.env };

describe("backend URL guard", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    process.env = { ...ORIGINAL_ENV };
    delete process.env.BACKEND_INTERNAL_URL;
    delete process.env.ALLOW_DOCKER_BACKEND_INTERNAL_URL;
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    process.env = { ...ORIGINAL_ENV };
  });

  it("accepts public HTTPS backend origins", () => {
    expect(parseBackendInternalUrl("https://api.naruon.net").origin).toBe(
      "https://api.naruon.net",
    );
  });

  it("rejects private IPv4 and IPv4-mapped IPv6 backend origins", () => {
    for (const url of [
      "https://127.0.0.1",
      "https://10.0.0.4",
      "https://192.168.1.10",
      "https://172.16.0.9",
      "https://169.254.169.254",
      "https://[::ffff:127.0.0.1]",
      "https://[::ffff:10.0.0.1]",
      "https://[::ffff:192.168.0.1]",
      "https://[::ffff:172.16.0.1]",
      "https://[::ffff:169.254.1.1]",
    ]) {
      expect(() => parseBackendInternalUrl(url), url).toThrow(
        "private/loopback/link-local",
      );
    }
  });

  it("allows the exact Compose backend URL only with the explicit opt-in", () => {
    expect(() => parseBackendInternalUrl("http://backend:8000")).toThrow(
      "https://",
    );
    process.env.ALLOW_DOCKER_BACKEND_INTERNAL_URL = "1";
    expect(parseBackendInternalUrl("http://backend:8000").origin).toBe(
      "http://backend:8000",
    );
  });

  it("requires a runtime backend origin in production", () => {
    vi.stubEnv("NODE_ENV", "production");
    expect(() => backendApiBaseUrl()).toThrow("production runtime");
  });
});
