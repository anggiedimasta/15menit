import type { GeocodeResult } from "@/lib/api";

import { LocationSearchInput } from "./LocationSearchInput";

type SearchBarProps = {
  onSelect: (result: GeocodeResult) => void;
};

/** @deprecated Prefer LocationSearchInput or CommuteRouteInputs */
export function SearchBar({ onSelect }: SearchBarProps) {
  return (
    <LocationSearchInput
      label="Cari lokasi"
      placeholder="Cari lokasi…"
      onSelect={onSelect}
    />
  );
}
