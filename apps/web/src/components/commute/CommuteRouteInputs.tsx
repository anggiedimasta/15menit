import { ArrowsDownUp } from "@phosphor-icons/react";

import { LocationSearchInput } from "@/components/geocode/LocationSearchInput";
import { Button } from "@/components/ui/button";
import { SimpleTooltip } from "@/components/ui/tooltip";
import type { GeocodeResult } from "@/lib/api";
import type { MapTheme } from "@/lib/mapStyles";
import { cn } from "@/lib/utils";

type CommuteRouteInputsProps = {
  dariLabel?: string;
  keLabel?: string;
  mapTheme?: MapTheme;
  onDariSelect: (result: GeocodeResult) => void;
  onKeSelect: (result: GeocodeResult) => void;
  onSwap: () => void;
};

export function CommuteRouteInputs({
  dariLabel = "",
  keLabel = "",
  mapTheme = "light",
  onDariSelect,
  onKeSelect,
  onSwap,
}: CommuteRouteInputsProps) {
  return (
    <div className="flex gap-2" data-testid="commute-route-inputs">
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <LocationSearchInput
          label="Dari"
          placeholder="Dari"
          value={dariLabel}
          pinColor="green"
          variant="glass"
          mapTheme={mapTheme}
          onSelect={onDariSelect}
          data-testid="commute-dari-search"
        />
        <div
          className={cn(
            "h-px",
            mapTheme === "dark" ? "bg-white/15" : "bg-border",
          )}
        />
        <LocationSearchInput
          label="Ke"
          placeholder="Ke"
          value={keLabel}
          pinColor="red"
          variant="glass"
          mapTheme={mapTheme}
          onSelect={onKeSelect}
          data-testid="commute-ke-search"
        />
      </div>
      <SimpleTooltip label="Tukar Dari dan Ke">
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          className={cn(
            "mt-1 shrink-0 self-start",
            mapTheme === "dark"
              ? "text-zinc-100 hover:bg-white/10 hover:text-white"
              : "text-foreground hover:bg-foreground/5 hover:text-foreground",
          )}
          onClick={onSwap}
          aria-label="Tukar Dari dan Ke"
          data-testid="swap-pins-button"
        >
          <ArrowsDownUp className="size-4" />
        </Button>
      </SimpleTooltip>
    </div>
  );
}
