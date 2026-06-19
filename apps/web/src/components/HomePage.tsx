import {
  ArrowsHorizontal,
  Car,
  MapPinArea,
  Moon,
  PersonSimpleWalk,
  Scales,
  Sun,
} from "@phosphor-icons/react";
import { getRouteApi } from "@tanstack/react-router";
import {
  startTransition,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { toast } from "sonner";

import { CommuteRouteInputs } from "@/components/commute/CommuteRouteInputs";
import { ComparisonCards } from "@/components/commute/ComparisonCards";
import { LocationSearchInput } from "@/components/geocode/LocationSearchInput";
import { MapView } from "@/components/map/MapView";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass-panel";
import { Slider } from "@/components/ui/slider";
import { Toaster } from "@/components/ui/sonner";
import { SimpleTooltip, TooltipProvider } from "@/components/ui/tooltip";
import { useApiHealth } from "@/hooks/useApiHealth";
import { useCommutePins } from "@/hooks/useCommutePins";
import {
  type CommuteCompareResponse,
  compareCommute,
  fetchCarIsochrone,
  fetchCityMeta,
  fetchWalkIsochrone,
  type GeocodeResult,
  type IsochroneFeature,
  type LatLng,
} from "@/lib/api";
import type { MapTheme } from "@/lib/mapStyles";
import {
  buildShareSearch,
  parseShareState,
  shareSearchEqual,
} from "@/lib/shareUrl";
import { APP_VERSION, cn } from "@/lib/utils";

const routeApi = getRouteApi("/");
const MINUTE_OPTIONS = [10, 15, 30, 45, 60];
type IsochroneTransport = "walk" | "car";

function applyIsochroneFeature(
  feature: IsochroneFeature,
  setPolygon: (polygon: GeoJSON.Polygon | null) => void,
  setIsoSource: (source: string | null) => void,
) {
  setPolygon(feature.geometry);
  setIsoSource(feature.properties.source === "mock" ? "mock" : "valhalla");
}

function fetchIsochrone(
  transport: IsochroneTransport,
  point: LatLng,
  minutes: number,
) {
  return transport === "car"
    ? fetchCarIsochrone(point, minutes)
    : fetchWalkIsochrone(point, minutes);
}

function coordLabel(point: LatLng): string {
  return `${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}`;
}

function ModeChip({
  active,
  icon: Icon,
  label,
  mapTheme,
  onClick,
  testId,
}: {
  active: boolean;
  icon: typeof ArrowsHorizontal;
  label: string;
  mapTheme: MapTheme;
  onClick: () => void;
  testId: string;
}) {
  const isDark = mapTheme === "dark";
  return (
    <SimpleTooltip label={label}>
      <button
        type="button"
        role="tab"
        aria-selected={active}
        aria-label={label}
        data-testid={testId}
        data-state={active ? "active" : "inactive"}
        onClick={onClick}
        className={cn(
          "flex size-11 items-center justify-center rounded-xl transition-colors",
          isDark
            ? active
              ? "bg-white/20 text-white"
              : "text-zinc-400 hover:bg-white/10 hover:text-white"
            : active
              ? "bg-foreground/10 text-foreground"
              : "text-muted-foreground hover:bg-foreground/5 hover:text-foreground",
        )}
      >
        <Icon className="size-5" weight={active ? "fill" : "regular"} />
      </button>
    </SimpleTooltip>
  );
}

export function App() {
  const search = routeApi.useSearch();
  const navigate = routeApi.useNavigate();
  const shareState = useMemo(() => parseShareState(search), [search]);
  const [mode, setMode] = useState<"commute" | "isochrone">(shareState.mode);
  const [minutes, setMinutes] = useState(15);
  const [isoTransport, setIsoTransport] = useState<IsochroneTransport>("walk");
  const [center, setCenter] = useState<LatLng>(
    shareState.a ?? shareState.b ?? { lat: -6.2, lng: 106.82 },
  );
  const [isoPin, setIsoPin] = useState<LatLng | null>(null);
  const [isoPinLabel, setIsoPinLabel] = useState("");
  const [polygon, setPolygon] = useState<GeoJSON.Polygon | null>(null);
  const [isoSource, setIsoSource] = useState<string | null>(null);
  const [compareData, setCompareData] = useState<CommuteCompareResponse | null>(
    null,
  );
  const [expandedMode, setExpandedMode] = useState<string | null>(null);
  const [transitRouteLine, setTransitRouteLine] = useState<number[][] | null>(
    null,
  );
  const [transitAvailable, setTransitAvailable] = useState(true);
  const [routingMode, setRoutingMode] = useState<string | null>(null);
  const [valhallaReachable, setValhallaReachable] = useState(false);
  const [mapTheme, setMapTheme] = useState<MapTheme>("light");
  const [pinLabels, setPinLabels] = useState({ a: "", b: "" });
  const apiHealthy = useApiHealth();
  const { pins, setPin, placeNextPin, swapPins, nextPin } = useCommutePins({
    a: shareState.a,
    b: shareState.b,
  });

  useEffect(() => {
    setPinLabels((prev) => {
      const next = { ...prev };
      if (shareState.a && !prev.a) next.a = coordLabel(shareState.a);
      if (shareState.b && !prev.b) next.b = coordLabel(shareState.b);
      if (next.a === prev.a && next.b === prev.b) return prev;
      return next;
    });
  }, [shareState.a, shareState.b]);

  useEffect(() => {
    const next = buildShareSearch({ a: pins.a, b: pins.b, mode });
    const current = buildShareSearch(shareState);
    if (shareSearchEqual(next, current)) return;
    startTransition(() => {
      navigate({ search: next, replace: true });
    });
  }, [pins.a, pins.b, mode, navigate, shareState]);

  useEffect(() => {
    fetchCityMeta()
      .then((meta) => {
        setTransitAvailable(meta.transit_available);
        setRoutingMode(meta.routing_mode);
        setValhallaReachable(meta.valhalla_reachable);
      })
      .catch(() => {
        setTransitAvailable(true);
        setRoutingMode(null);
        setValhallaReachable(false);
      });
  }, []);

  const handleMapClick = useCallback(
    (point: LatLng) => {
      if (mode === "isochrone") {
        setIsoPin(point);
        setIsoPinLabel(coordLabel(point));
        fetchIsochrone(isoTransport, point, minutes)
          .then((feature) =>
            applyIsochroneFeature(feature, setPolygon, setIsoSource),
          )
          .catch((err: Error) => toast.error(err.message));
      } else {
        setPinLabels((prev) => ({
          ...prev,
          [nextPin]: coordLabel(point),
        }));
        placeNextPin(point);
      }
    },
    [mode, minutes, isoTransport, placeNextPin, nextPin],
  );

  const handleDariSelect = (result: GeocodeResult) => {
    const point = { lat: result.lat, lng: result.lng };
    setPin("a", point);
    setPinLabels((prev) => ({ ...prev, a: result.display_name }));
    setCenter(point);
    setCompareData(null);
  };

  const handleKeSelect = (result: GeocodeResult) => {
    const point = { lat: result.lat, lng: result.lng };
    setPin("b", point);
    setPinLabels((prev) => ({ ...prev, b: result.display_name }));
    setCenter(point);
    setCompareData(null);
  };

  const handleIsochroneSelect = (result: GeocodeResult) => {
    const point = { lat: result.lat, lng: result.lng };
    setCenter(point);
    setIsoPin(point);
    setIsoPinLabel(result.display_name);
    fetchIsochrone(isoTransport, point, minutes)
      .then((feature) =>
        applyIsochroneFeature(feature, setPolygon, setIsoSource),
      )
      .catch((err: Error) => toast.error(err.message));
  };

  const handleSwap = () => {
    swapPins();
    setPinLabels((prev) => ({ a: prev.b, b: prev.a }));
    setCompareData(null);
  };

  const handleCompare = () => {
    if (!pins.a || !pins.b) return;
    setExpandedMode(null);
    setTransitRouteLine(null);
    compareCommute(pins.a, pins.b)
      .then(setCompareData)
      .catch((err: Error) => toast.error(err.message));
  };

  const handleExpandMode = (
    expanded: string | null,
    polyline?: number[][] | null,
  ) => {
    setExpandedMode(expanded);
    setTransitRouteLine(expanded === "transit" ? (polyline ?? null) : null);
  };

  const setIsoTransportAndRefresh = (transport: IsochroneTransport) => {
    setIsoTransport(transport);
    if (isoPin) {
      fetchIsochrone(transport, isoPin, minutes)
        .then((feature) =>
          applyIsochroneFeature(feature, setPolygon, setIsoSource),
        )
        .catch((err: Error) => toast.error(err.message));
    }
  };

  return (
    <TooltipProvider>
      <Toaster />
      <div className="relative h-svh w-full overflow-hidden">
        <MapView
          center={center}
          pin={mode === "isochrone" ? isoPin : null}
          pinLabel="Asal"
          showOriginPulse={mode === "isochrone" && isoPin != null}
          pinA={mode === "commute" ? pins.a : null}
          pinALabel="Dari"
          pinB={mode === "commute" ? pins.b : null}
          pinBLabel="Ke"
          polygon={mode === "isochrone" ? polygon : null}
          routeLine={mode === "commute" ? transitRouteLine : null}
          theme={mapTheme}
          onThemeChange={setMapTheme}
          onClick={handleMapClick}
        />

        <div className="pointer-events-none fixed inset-0 z-10">
          <div
            className="pointer-events-auto fixed top-[max(1rem,env(safe-area-inset-top))] left-[max(1rem,env(safe-area-inset-left))] z-20 w-[min(calc(100%-2rem-3.5rem),24rem)]"
            data-testid="floating-top-panel"
          >
            <GlassPanel mapTheme={mapTheme} className="p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <h1 className="text-sm font-semibold tracking-tight">
                  15menit
                </h1>
                <div className="flex items-center gap-1">
                  <span
                    className={cn(
                      "text-[10px] tracking-wide",
                      mapTheme === "dark"
                        ? "text-zinc-400"
                        : "text-muted-foreground",
                    )}
                  >
                    v{APP_VERSION}
                  </span>
                  <SimpleTooltip
                    label={mapTheme === "light" ? "Mode gelap" : "Mode terang"}
                  >
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-xs"
                      className={cn(
                        mapTheme === "dark"
                          ? "text-zinc-200 hover:bg-white/10 hover:text-white"
                          : "text-foreground/80 hover:bg-foreground/5 hover:text-foreground",
                      )}
                      onClick={() =>
                        setMapTheme(mapTheme === "light" ? "dark" : "light")
                      }
                      data-testid="map-style-toggle"
                      aria-label={
                        mapTheme === "light" ? "Mode gelap" : "Mode terang"
                      }
                    >
                      {mapTheme === "light" ? (
                        <Moon className="size-3.5" weight="fill" />
                      ) : (
                        <Sun className="size-3.5" weight="fill" />
                      )}
                    </Button>
                  </SimpleTooltip>
                </div>
              </div>

              {!apiHealthy && (
                <div
                  className={cn(
                    "mb-2 rounded-lg border px-2 py-1.5 text-xs",
                    mapTheme === "dark"
                      ? "border-red-400/40 bg-red-500/20 text-red-100"
                      : "border-red-200 bg-red-50 text-red-800",
                  )}
                  data-testid="api-unreachable-banner"
                  role="alert"
                >
                  API tidak tersedia
                </div>
              )}

              {routingMode === "mock" && !valhallaReachable && apiHealthy && (
                <div
                  className={cn(
                    "mb-2 rounded-lg border px-2 py-1.5 text-xs",
                    mapTheme === "dark"
                      ? "border-sky-400/40 bg-sky-500/20 text-sky-100"
                      : "border-sky-200 bg-sky-50 text-sky-900",
                  )}
                  data-testid="routing-mock-banner"
                >
                  Mode simulasi — isochrone & rute jalan/mobil perkiraan, bukan
                  data OSM nyata
                </div>
              )}

              {!transitAvailable && mode === "commute" && (
                <div
                  className={cn(
                    "mb-2 rounded-lg border px-2 py-1.5 text-xs",
                    mapTheme === "dark"
                      ? "border-amber-400/40 bg-amber-500/20 text-amber-100"
                      : "border-amber-200 bg-amber-50 text-amber-900",
                  )}
                  data-testid="transit-unavailable-banner"
                >
                  Transit belum tersedia
                </div>
              )}

              {mode === "commute" ? (
                <div className="flex items-start gap-2">
                  <div className="min-w-0 flex-1">
                    <CommuteRouteInputs
                      dariLabel={pinLabels.a}
                      keLabel={pinLabels.b}
                      mapTheme={mapTheme}
                      onDariSelect={handleDariSelect}
                      onKeSelect={handleKeSelect}
                      onSwap={handleSwap}
                    />
                  </div>
                  <SimpleTooltip label="Bandingkan moda">
                    <Button
                      type="button"
                      size="icon"
                      className={cn(
                        "mt-1 shrink-0",
                        mapTheme === "dark"
                          ? "bg-white/20 text-white hover:bg-white/30"
                          : "bg-primary text-primary-foreground hover:bg-primary/90",
                      )}
                      disabled={!pins.a || !pins.b}
                      onClick={handleCompare}
                      aria-label="Bandingkan moda"
                      data-testid="compare-button"
                    >
                      <Scales className="size-4" weight="bold" />
                    </Button>
                  </SimpleTooltip>
                </div>
              ) : (
                <LocationSearchInput
                  label="Asal"
                  placeholder="Asal"
                  value={isoPinLabel}
                  pinColor="indigo"
                  variant="glass"
                  mapTheme={mapTheme}
                  onSelect={handleIsochroneSelect}
                  data-testid="isochrone-origin-search"
                />
              )}
            </GlassPanel>
          </div>

          <div className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-col">
            {compareData && mode === "commute" && (
              <div className="pointer-events-auto pl-4 pr-14 pb-2">
                <ComparisonCards
                  data={compareData}
                  variant="floating"
                  mapTheme={mapTheme}
                  expandedMode={expandedMode}
                  onExpandMode={handleExpandMode}
                />
              </div>
            )}

            {mode === "isochrone" && (
              <div
                className="pointer-events-auto pl-4 pr-14 pb-2"
                role="tabpanel"
                aria-label="Isochrone"
              >
                <GlassPanel mapTheme={mapTheme} className="space-y-3 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex gap-1">
                      <SimpleTooltip label="Jalan kaki">
                        <Button
                          type="button"
                          size="icon-sm"
                          variant="ghost"
                          className={cn(
                            mapTheme === "dark"
                              ? "text-zinc-200 hover:bg-white/10 hover:text-white"
                              : "text-foreground/80 hover:bg-foreground/5 hover:text-foreground",
                            isoTransport === "walk" &&
                              (mapTheme === "dark"
                                ? "bg-white/20 text-white"
                                : "bg-foreground/10 text-foreground"),
                          )}
                          onClick={() => setIsoTransportAndRefresh("walk")}
                          aria-label="Jalan kaki"
                          data-testid="iso-transport-walk"
                        >
                          <PersonSimpleWalk className="size-4" weight="fill" />
                        </Button>
                      </SimpleTooltip>
                      <SimpleTooltip label="Mobil">
                        <Button
                          type="button"
                          size="icon-sm"
                          variant="ghost"
                          className={cn(
                            mapTheme === "dark"
                              ? "text-zinc-200 hover:bg-white/10 hover:text-white"
                              : "text-foreground/80 hover:bg-foreground/5 hover:text-foreground",
                            isoTransport === "car" &&
                              (mapTheme === "dark"
                                ? "bg-white/20 text-white"
                                : "bg-foreground/10 text-foreground"),
                          )}
                          onClick={() => setIsoTransportAndRefresh("car")}
                          aria-label="Mobil"
                          data-testid="iso-transport-car"
                        >
                          <Car className="size-4" weight="fill" />
                        </Button>
                      </SimpleTooltip>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className="text-sm font-semibold tracking-tight"
                        data-testid="iso-minutes-label"
                      >
                        {minutes}′
                      </span>
                      {isoSource === "mock" && (
                        <Badge
                          variant="outline"
                          className={
                            mapTheme === "dark"
                              ? "border-white/20 text-zinc-200"
                              : undefined
                          }
                          data-testid="iso-mock-badge"
                        >
                          Simulasi
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Slider
                    min={0}
                    max={MINUTE_OPTIONS.length - 1}
                    step={1}
                    value={[MINUTE_OPTIONS.indexOf(minutes)]}
                    onValueChange={([idx]) => {
                      const next = MINUTE_OPTIONS[idx ?? 1] ?? 15;
                      setMinutes(next);
                      if (isoPin) {
                        fetchIsochrone(isoTransport, isoPin, next)
                          .then((feature) =>
                            applyIsochroneFeature(
                              feature,
                              setPolygon,
                              setIsoSource,
                            ),
                          )
                          .catch((err: Error) => toast.error(err.message));
                      }
                    }}
                  />
                </GlassPanel>
              </div>
            )}

            <div className="pointer-events-auto pl-4 pr-14 pb-[max(1rem,env(safe-area-inset-bottom))]">
              <GlassPanel
                mapTheme={mapTheme}
                className="mx-auto flex w-fit gap-1 p-1"
              >
                <ModeChip
                  active={mode === "commute"}
                  icon={ArrowsHorizontal}
                  label="Commute"
                  mapTheme={mapTheme}
                  testId="mode-commute"
                  onClick={() => setMode("commute")}
                />
                <ModeChip
                  active={mode === "isochrone"}
                  icon={MapPinArea}
                  label="Isochrone"
                  mapTheme={mapTheme}
                  testId="mode-isochrone"
                  onClick={() => setMode("isochrone")}
                />
              </GlassPanel>
            </div>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
