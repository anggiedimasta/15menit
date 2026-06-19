/** Shared API response shapes between web and api. */

export type HealthResponse = {
  status: "ok";
};

export type CommuteMode = "walking" | "transit" | "car" | "motorcycle";

export type LatLng = {
  lat: number;
  lng: number;
};

export type CommuteModeResult = {
  mode: CommuteMode;
  duration_min: number;
  distance_m?: number;
  transfers?: number;
  cost_idr?: number | null;
  is_fastest?: boolean;
};

export type CommuteCompareResponse = {
  fastest_mode: CommuteMode;
  note?: string | null;
  transit_available: boolean;
  results: CommuteModeResult[];
};

export type CityMeta = {
  city: string;
  transit_available: boolean;
  routing_mode: string;
};
