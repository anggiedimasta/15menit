import { useCallback, useEffect, useState } from "react";

import type { LatLng } from "@/lib/api";

const STORAGE_KEY = "15menit.commute.pins";

type Pins = { a: LatLng | null; b: LatLng | null };

function loadPins(): Pins {
  if (typeof window === "undefined") return { a: null, b: null };
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Pins) : { a: null, b: null };
  } catch {
    return { a: null, b: null };
  }
}

export function useCommutePins(initial?: Pins) {
  const [pins, setPins] = useState<Pins>(() => {
    if (initial?.a || initial?.b) {
      return { a: initial.a ?? null, b: initial.b ?? null };
    }
    return loadPins();
  });
  const [nextPin, setNextPin] = useState<"a" | "b">(() => {
    if (initial?.a && !initial?.b) return "b";
    if (!initial?.a && initial?.b) return "a";
    return "a";
  });

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(pins));
  }, [pins]);

  const setPin = useCallback((label: "a" | "b", point: LatLng) => {
    setPins((prev) => ({ ...prev, [label]: point }));
  }, []);

  const placeNextPin = useCallback(
    (point: LatLng) => {
      setPin(nextPin, point);
      setNextPin(nextPin === "a" ? "b" : "a");
    },
    [nextPin, setPin],
  );

  const swapPins = useCallback(() => {
    setPins((prev) => ({ a: prev.b, b: prev.a }));
  }, []);

  const clearPins = useCallback(() => {
    setPins({ a: null, b: null });
    setNextPin("a");
  }, []);

  return { pins, nextPin, setPin, placeNextPin, swapPins, clearPins };
}
