import maplibregl from "maplibre-gl";
import { useCallback, useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";

import type { LatLng } from "@/lib/api";
import { MAP_STYLES, type MapTheme } from "@/lib/mapStyles";

type MapViewProps = {
  center?: LatLng;
  pin?: LatLng | null;
  pinLabel?: string;
  showOriginPulse?: boolean;
  pinA?: LatLng | null;
  pinALabel?: string;
  pinB?: LatLng | null;
  pinBLabel?: string;
  polygon?: GeoJSON.Polygon | null;
  routeLine?: number[][] | null;
  theme?: MapTheme;
  onThemeChange?: (theme: MapTheme) => void;
  onClick?: (point: LatLng) => void;
};

const DEFAULT_CENTER: LatLng = { lat: -6.2, lng: 106.82 };

function createPinMarkerElement(
  badge: string,
  color: string,
  sublabel?: string,
  pulse = false,
  markerId = "pin",
): HTMLElement {
  const wrap = document.createElement("div");
  wrap.className = "pointer-events-none flex flex-col items-center gap-0.5";
  wrap.setAttribute("data-testid", `map-marker-${markerId}`);

  const pinWrap = document.createElement("div");
  pinWrap.className = "relative flex items-center justify-center";

  if (pulse) {
    const pulseRing = document.createElement("div");
    pulseRing.className =
      "absolute size-10 rounded-full bg-indigo-400/40 animate-ping";
    pinWrap.appendChild(pulseRing);
  }

  const pin = document.createElement("div");
  pin.className =
    "relative flex size-8 items-center justify-center rounded-full border-2 border-white text-xs font-bold text-white shadow-md";
  pin.style.backgroundColor = color;
  pin.textContent = badge.length <= 2 ? badge : "●";
  pinWrap.appendChild(pin);
  wrap.appendChild(pinWrap);

  const caption = document.createElement("span");
  caption.className =
    "rounded bg-white/95 px-1.5 py-0.5 text-[10px] font-semibold text-foreground shadow-sm";
  caption.textContent = sublabel ?? badge;
  wrap.appendChild(caption);

  return wrap;
}

export function MapView({
  center = DEFAULT_CENTER,
  pin,
  pinLabel = "Asal",
  showOriginPulse = false,
  pinA,
  pinALabel = "A",
  pinB,
  pinBLabel = "B",
  polygon,
  routeLine,
  theme = "light",
  onThemeChange: _onThemeChange,
  onClick,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<{
    origin: maplibregl.Marker | null;
    a: maplibregl.Marker | null;
    b: maplibregl.Marker | null;
  }>({ origin: null, a: null, b: null });
  const onClickRef = useRef(onClick);
  onClickRef.current = onClick;

  const applyPolygonAndRoute = useCallback(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) return;

    if (map.getLayer("iso-layer")) map.removeLayer("iso-layer");
    if (map.getLayer("iso-outline")) map.removeLayer("iso-outline");
    if (map.getSource("iso-source")) map.removeSource("iso-source");
    if (polygon) {
      map.addSource("iso-source", {
        type: "geojson",
        data: { type: "Feature", geometry: polygon, properties: {} },
      });
      map.addLayer({
        id: "iso-layer",
        type: "fill",
        source: "iso-source",
        paint: {
          "fill-color": "#6366f1",
          "fill-opacity": 0.25,
        },
      });
      map.addLayer({
        id: "iso-outline",
        type: "line",
        source: "iso-source",
        paint: { "line-color": "#4338ca", "line-width": 2 },
      });
    }

    if (map.getLayer("route-layer")) map.removeLayer("route-layer");
    if (map.getSource("route-source")) map.removeSource("route-source");
    if (routeLine && routeLine.length >= 2) {
      map.addSource("route-source", {
        type: "geojson",
        data: {
          type: "Feature",
          geometry: { type: "LineString", coordinates: routeLine },
          properties: {},
        },
      });
      map.addLayer({
        id: "route-layer",
        type: "line",
        source: "route-source",
        paint: {
          "line-color": "#2563eb",
          "line-width": 4,
          "line-opacity": 0.85,
        },
      });
    }
  }, [polygon, routeLine]);

  const applyPolygonRef = useRef(applyPolygonAndRoute);
  applyPolygonRef.current = applyPolygonAndRoute;
  const themeReadyRef = useRef(false);
  const initialCenterRef = useRef(center);
  const initialThemeRef = useRef(theme);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLES[initialThemeRef.current],
      center: [initialCenterRef.current.lng, initialCenterRef.current.lat],
      zoom: 12,
    });
    map.addControl(new maplibregl.NavigationControl(), "bottom-right");
    map.on("click", (event) => {
      onClickRef.current?.({ lat: event.lngLat.lat, lng: event.lngLat.lng });
    });
    const onStyleReady = () => applyPolygonRef.current();
    map.on("load", onStyleReady);
    map.on("style.load", onStyleReady);
    mapRef.current = map;

    return () => {
      map.off("load", onStyleReady);
      map.off("style.load", onStyleReady);
      for (const marker of Object.values(markersRef.current)) {
        marker?.remove();
      }
      markersRef.current = { origin: null, a: null, b: null };
      map.remove();
      mapRef.current = null;
      themeReadyRef.current = false;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.flyTo({ center: [center.lng, center.lat], essential: true });
  }, [center.lat, center.lng]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (!themeReadyRef.current) {
      themeReadyRef.current = true;
      return;
    }
    map.setStyle(MAP_STYLES[theme]);
  }, [theme]);

  useEffect(() => {
    applyPolygonAndRoute();
  }, [applyPolygonAndRoute]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const upsert = (
      key: "origin" | "a" | "b",
      point: LatLng | null | undefined,
      el: HTMLElement | null,
    ) => {
      markersRef.current[key]?.remove();
      markersRef.current[key] = null;
      if (!point || !el) return;
      markersRef.current[key] = new maplibregl.Marker({ element: el })
        .setLngLat([point.lng, point.lat])
        .addTo(map);
    };

    upsert(
      "origin",
      pin,
      pin
        ? createPinMarkerElement(
            "●",
            "#6366f1",
            pinLabel,
            showOriginPulse,
            "titik-asal",
          )
        : null,
    );
    upsert(
      "a",
      pinA,
      pinA
        ? createPinMarkerElement("A", "#22c55e", pinALabel, false, "dari")
        : null,
    );
    upsert(
      "b",
      pinB,
      pinB
        ? createPinMarkerElement("B", "#ef4444", pinBLabel, false, "ke")
        : null,
    );
  }, [pin, pinLabel, showOriginPulse, pinA, pinALabel, pinB, pinBLabel]);

  return (
    <div className="relative h-full w-full" data-testid="map-container">
      <div ref={containerRef} className="h-full w-full" data-testid="map" />
    </div>
  );
}
