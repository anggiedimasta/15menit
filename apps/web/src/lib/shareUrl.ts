import type { LatLng } from "@/lib/api";

export type AppMode = "commute" | "isochrone";

export type ShareState = {
  a: LatLng | null;
  b: LatLng | null;
  mode: AppMode;
};

const COORD_RE = /^-?\d+(\.\d+)?,-?\d+(\.\d+)?$/;

function parseCoord(raw: string | undefined): LatLng | null {
  if (!raw || !COORD_RE.test(raw)) return null;
  const [latStr, lngStr] = raw.split(",");
  const lat = Number(latStr);
  const lng = Number(lngStr);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return null;
  return { lat, lng };
}

export function parseShareState(search: {
  a?: string;
  b?: string;
  mode?: string;
}): ShareState {
  const mode: AppMode = search.mode === "isochrone" ? "isochrone" : "commute";
  return {
    a: parseCoord(search.a),
    b: parseCoord(search.b),
    mode,
  };
}

export function formatCoord(point: LatLng): string {
  return `${point.lat.toFixed(5)},${point.lng.toFixed(5)}`;
}

export function buildShareSearch(state: ShareState): {
  a?: string;
  b?: string;
  mode?: AppMode;
} {
  const search: { a?: string; b?: string; mode?: AppMode } = {};
  if (state.a) search.a = formatCoord(state.a);
  if (state.b) search.b = formatCoord(state.b);
  if (state.mode !== "commute") search.mode = state.mode;
  return search;
}
