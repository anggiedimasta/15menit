export const API_URL =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? "/api" : "http://localhost:8000");

const API_UNREACHABLE_MESSAGE =
  "Server tidak dapat dihubungi. Pastikan API berjalan (bun run dev:api).";

export type LatLng = { lat: number; lng: number };

export type IsochroneFeature = {
  type: "Feature";
  geometry: GeoJSON.Polygon;
  properties: Record<string, unknown>;
};

export type GeocodeResult = {
  lat: number;
  lng: number;
  display_name: string;
};

export type CommuteModeResult = {
  mode: "walking" | "transit" | "car" | "motorcycle";
  duration_min: number;
  distance_m?: number;
  transfers?: number;
  cost_idr?: number | null;
  is_fastest?: boolean;
  route_polyline?: number[][] | null;
  legs?: Array<{
    mode: string;
    route_id?: string;
    line_name?: string;
    board_stop?: string;
    alight_stop?: string;
    duration_min?: number;
  }>;
  fare_breakdown?: Array<Record<string, unknown>>;
};

export type CommuteCompareResponse = {
  fastest_mode: string;
  note?: string | null;
  transit_available: boolean;
  results: CommuteModeResult[];
};

export type CityMeta = {
  city: string;
  transit_available: boolean;
  routing_mode: string;
  valhalla_reachable: boolean;
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new Error(API_UNREACHABLE_MESSAGE);
  }
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body.trim() || `Permintaan gagal (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: "GET",
      signal: AbortSignal.timeout(5_000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export function fetchWalkIsochrone(
  point: LatLng,
  minutes: number,
): Promise<IsochroneFeature> {
  return apiFetch("/isochrone/walk", {
    method: "POST",
    body: JSON.stringify({ ...point, minutes }),
  });
}

export function fetchCarIsochrone(
  point: LatLng,
  minutes: number,
): Promise<IsochroneFeature> {
  return apiFetch("/isochrone/car", {
    method: "POST",
    body: JSON.stringify({ ...point, minutes }),
  });
}

export function searchGeocode(query: string): Promise<GeocodeResult[]> {
  return apiFetch(`/geocode/search?q=${encodeURIComponent(query)}`);
}

export function compareCommute(
  origin: LatLng,
  destination: LatLng,
): Promise<CommuteCompareResponse> {
  return apiFetch("/commute/compare", {
    method: "POST",
    body: JSON.stringify({ origin, destination }),
  });
}

export function fetchCityMeta(): Promise<CityMeta> {
  return apiFetch("/meta/city");
}
