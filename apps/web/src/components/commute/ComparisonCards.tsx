import {
  Bicycle,
  Bus,
  Car,
  CaretDown,
  Crown,
  PersonSimpleWalk,
} from "@phosphor-icons/react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass-panel";
import { SimpleTooltip } from "@/components/ui/tooltip";
import type { CommuteCompareResponse } from "@/lib/api";
import type { MapTheme } from "@/lib/mapStyles";
import { cn } from "@/lib/utils";

const MODE_LABELS: Record<string, string> = {
  walking: "Jalan kaki",
  transit: "Transit",
  car: "Mobil",
  motorcycle: "Motor",
};

const MODE_ICONS: Record<string, typeof PersonSimpleWalk> = {
  walking: PersonSimpleWalk,
  transit: Bus,
  car: Car,
  motorcycle: Bicycle,
};

const LEG_MODE_LABELS: Record<string, string> = {
  walk: "Jalan",
  bus: "Bus",
  rail: "KRL",
  subway: "MRT",
};

type ComparisonCardsProps = {
  data: CommuteCompareResponse | null;
  expandedMode?: string | null;
  onExpandMode?: (mode: string | null, polyline?: number[][] | null) => void;
  variant?: "default" | "floating";
  mapTheme?: MapTheme;
};

export function ComparisonCards({
  data,
  expandedMode,
  onExpandMode,
  variant = "default",
  mapTheme = "light",
}: ComparisonCardsProps) {
  const [expanded, setExpanded] = useState<string | null>(expandedMode ?? null);
  const isFloating = variant === "floating";

  useEffect(() => {
    setExpanded(expandedMode ?? null);
  }, [expandedMode]);

  if (!data) return null;

  const toggleExpand = (mode: string, polyline?: number[][] | null) => {
    const next = expanded === mode ? null : mode;
    setExpanded(next);
    onExpandMode?.(next, next ? (polyline ?? null) : null);
  };

  if (isFloating) {
    const isDark = mapTheme === "dark";
    return (
      <GlassPanel
        mapTheme={mapTheme}
        className="p-3"
        data-testid="comparison-cards"
      >
        {data.note && (
          <p
            className={cn(
              "mb-2 text-xs",
              isDark ? "text-zinc-300" : "text-muted-foreground",
            )}
          >
            {data.note}
          </p>
        )}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {data.results.map((result) => {
            const Icon = MODE_ICONS[result.mode] ?? PersonSimpleWalk;
            const label = MODE_LABELS[result.mode] ?? result.mode;
            const hasLegs =
              result.mode === "transit" && (result.legs?.length ?? 0) > 0;
            const isExpanded = expanded === result.mode;

            return (
              <SimpleTooltip key={result.mode} label={label}>
                <button
                  type="button"
                  data-testid={`comparison-card-${result.mode}`}
                  className={cn(
                    "flex min-w-[4.5rem] shrink-0 flex-col items-center gap-1 rounded-xl border px-3 py-2 transition-colors",
                    isDark
                      ? "border-white/15 bg-white/10 text-zinc-50"
                      : "border-zinc-200 bg-white/80 text-zinc-900",
                    result.is_fastest &&
                      (isDark
                        ? "border-emerald-400/60 bg-emerald-500/20"
                        : "border-emerald-500/50 bg-emerald-500/10"),
                    isExpanded &&
                      (isDark
                        ? "ring-2 ring-white/30"
                        : "ring-2 ring-primary/30"),
                  )}
                  onClick={() => {
                    if (hasLegs) {
                      toggleExpand(result.mode, result.route_polyline ?? null);
                    }
                  }}
                  aria-label={`${label}, ${result.duration_min} menit`}
                  aria-expanded={hasLegs ? isExpanded : undefined}
                >
                  <Icon className="size-5" aria-hidden />
                  <span className="text-lg font-semibold leading-none tracking-tight">
                    {result.duration_min}
                  </span>
                  <span
                    className={cn(
                      "text-[10px] uppercase tracking-wider",
                      isDark ? "text-zinc-400" : "text-zinc-600",
                    )}
                  >
                    mnt
                  </span>
                  {result.is_fastest && (
                    <Crown
                      className={cn(
                        "size-3",
                        isDark ? "text-emerald-300" : "text-emerald-600",
                      )}
                      weight="fill"
                      aria-label="Paling cepat"
                    />
                  )}
                  {hasLegs && (
                    <CaretDown
                      className={cn(
                        "size-3",
                        isDark ? "text-zinc-400" : "text-zinc-600",
                        isExpanded && "rotate-180",
                      )}
                      aria-hidden
                    />
                  )}
                </button>
              </SimpleTooltip>
            );
          })}
        </div>
        {expanded === "transit" && (
          <ol
            className={cn(
              "mt-3 space-y-1 border-t pt-3 text-xs",
              isDark
                ? "border-white/15 text-zinc-200"
                : "border-border text-foreground/80",
            )}
          >
            {data.results
              .find((r) => r.mode === "transit")
              ?.legs?.map((leg) => (
                <li
                  key={`${leg.mode}-${leg.board_stop ?? ""}-${leg.alight_stop ?? ""}-${leg.route_id ?? ""}`}
                >
                  {LEG_MODE_LABELS[leg.mode as string] ?? leg.mode}
                  {leg.line_name ? ` — ${leg.line_name}` : ""}
                  {leg.board_stop ? `: ${leg.board_stop}` : ""}
                  {leg.alight_stop ? ` → ${leg.alight_stop}` : ""}
                  {leg.duration_min != null ? ` (${leg.duration_min} mnt)` : ""}
                </li>
              ))}
          </ol>
        )}
        <span className="sr-only" data-testid="fastest-badge">
          {data.results.some((r) => r.is_fastest) ? "Paling cepat" : ""}
        </span>
      </GlassPanel>
    );
  }

  return (
    <div className="flex flex-col gap-3" data-testid="comparison-cards">
      {data.note && (
        <p className="text-sm text-muted-foreground">{data.note}</p>
      )}
      {data.results.map((result) => {
        const isExpanded = expanded === result.mode;
        const hasLegs =
          result.mode === "transit" && (result.legs?.length ?? 0) > 0;
        const Icon = MODE_ICONS[result.mode] ?? PersonSimpleWalk;

        return (
          <div
            key={result.mode}
            data-testid={`comparison-card-${result.mode}`}
            className={cn(
              "rounded-xl border p-4",
              result.is_fastest &&
                "border-emerald-500 bg-emerald-500/5 ring-2 ring-emerald-500/40",
            )}
          >
            <div className="flex items-center justify-between pb-2">
              <div className="flex items-center gap-2 text-base font-medium">
                <Icon className="size-5 shrink-0" aria-hidden />
                {MODE_LABELS[result.mode] ?? result.mode}
              </div>
              {result.is_fastest && (
                <span className="text-xs font-medium text-emerald-600">
                  Paling cepat
                </span>
              )}
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-lg font-semibold">
                {result.duration_min} menit
              </p>
              {result.distance_m != null && (
                <p className="text-muted-foreground">
                  {(result.distance_m / 1000).toFixed(1)} km
                </p>
              )}
              {result.cost_idr != null && (
                <p className="font-medium">
                  Rp {result.cost_idr.toLocaleString("id-ID")}
                </p>
              )}
              {hasLegs && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-auto px-0 text-xs"
                    onClick={() =>
                      toggleExpand(result.mode, result.route_polyline ?? null)
                    }
                  >
                    {isExpanded ? "Sembunyikan rute" : "Lihat langkah transit"}
                  </Button>
                  {isExpanded && (
                    <ol className="list-decimal space-y-1 pl-4 text-xs">
                      {result.legs?.map((leg) => (
                        <li
                          key={`${leg.mode}-${leg.board_stop ?? ""}-${leg.alight_stop ?? ""}-${leg.route_id ?? ""}`}
                        >
                          {LEG_MODE_LABELS[leg.mode as string] ?? leg.mode}
                          {leg.line_name ? ` — ${leg.line_name}` : ""}
                          {leg.board_stop ? `: ${leg.board_stop}` : ""}
                          {leg.alight_stop ? ` → ${leg.alight_stop}` : ""}
                          {leg.duration_min != null
                            ? ` (${leg.duration_min} mnt)`
                            : ""}
                        </li>
                      ))}
                    </ol>
                  )}
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
