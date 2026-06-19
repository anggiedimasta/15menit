import { describe, expect, it } from "vitest";

import {
  buildShareSearch,
  formatCoord,
  parseShareState,
  shareSearchEqual,
} from "@/lib/shareUrl";

describe("shareUrl", () => {
  it("parses commute pins from query", () => {
    const state = parseShareState({
      a: "-6.17540,106.82720",
      b: "-6.20880,106.84560",
      mode: "commute",
    });
    expect(state.a).toEqual({ lat: -6.1754, lng: 106.8272 });
    expect(state.b).toEqual({ lat: -6.2088, lng: 106.8456 });
    expect(state.mode).toBe("commute");
  });

  it("rejects invalid coordinates", () => {
    const state = parseShareState({ a: "invalid", b: "1,2,3" });
    expect(state.a).toBeNull();
    expect(state.b).toBeNull();
  });

  it("builds share search from pins", () => {
    const search = buildShareSearch({
      a: { lat: -6.2, lng: 106.82 },
      b: { lat: -6.21, lng: 106.85 },
      mode: "commute",
    });
    expect(search.a).toBe(formatCoord({ lat: -6.2, lng: 106.82 }));
    expect(search.b).toBe(formatCoord({ lat: -6.21, lng: 106.85 }));
    expect(search.mode).toBeUndefined();
  });

  it("includes isochrone mode in share search", () => {
    const search = buildShareSearch({
      a: null,
      b: null,
      mode: "isochrone",
    });
    expect(search.mode).toBe("isochrone");
  });

  it("compares share search params", () => {
    const left = buildShareSearch({
      a: { lat: -6.2, lng: 106.82 },
      b: null,
      mode: "commute",
    });
    const right = { ...left };
    expect(shareSearchEqual(left, right)).toBe(true);
    expect(shareSearchEqual(left, { ...left, mode: "isochrone" })).toBe(false);
  });
});
