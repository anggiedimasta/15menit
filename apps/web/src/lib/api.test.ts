import { afterEach, describe, expect, it, vi } from "vitest";

describe("checkApiHealth", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("returns true when health endpoint responds ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(null, { status: 200 }))),
    );
    const { checkApiHealth } = await import("@/lib/api");
    await expect(checkApiHealth()).resolves.toBe(true);
  });

  it("returns false when fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new Error("offline"))),
    );
    const { checkApiHealth } = await import("@/lib/api");
    await expect(checkApiHealth()).resolves.toBe(false);
  });
});

describe("apiFetch network errors", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("throws friendly message when server unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );
    const { fetchCityMeta } = await import("@/lib/api");
    await expect(fetchCityMeta()).rejects.toThrow(
      /Server tidak dapat dihubungi/,
    );
  });
});
