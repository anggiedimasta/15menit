import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { fetchCityMeta, checkApiHealth } = vi.hoisted(() => ({
  fetchCityMeta: vi.fn(() =>
    Promise.resolve({
      city: "jakarta",
      transit_available: true,
      routing_mode: "mock",
      valhalla_reachable: false,
    }),
  ),
  checkApiHealth: vi.fn(() => Promise.resolve(true)),
}));

vi.mock("maplibre-gl", () => {
  class MapLibreMap {
    addControl = vi.fn();
    on = vi.fn();
    off = vi.fn();
    flyTo = vi.fn();
    setStyle = vi.fn();
    isStyleLoaded = vi.fn(() => true);
    getLayer = vi.fn();
    getSource = vi.fn();
    removeLayer = vi.fn();
    removeSource = vi.fn();
    addSource = vi.fn();
    addLayer = vi.fn();
    once = vi.fn();
    remove = vi.fn();
  }
  class NavigationControl {}
  class Marker {
    setLngLat = vi.fn().mockReturnThis();
    addTo = vi.fn().mockReturnThis();
    remove = vi.fn();
  }
  return { default: { Map: MapLibreMap, NavigationControl, Marker } };
});

vi.mock("@/lib/supabase", () => ({
  fetchGeocodeCache: vi.fn(() => Promise.resolve(null)),
}));

vi.mock("@/lib/api", () => ({
  fetchCityMeta,
  checkApiHealth,
  fetchWalkIsochrone: vi.fn(() =>
    Promise.resolve({
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [] },
      properties: {},
    }),
  ),
  fetchCarIsochrone: vi.fn(() =>
    Promise.resolve({
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [] },
      properties: {},
    }),
  ),
  compareCommute: vi.fn(),
  searchGeocode: vi.fn(() => Promise.resolve([])),
}));

vi.mock("@tanstack/react-router", () => ({
  getRouteApi: () => ({
    useSearch: () => ({}),
    useNavigate: () => vi.fn(),
  }),
}));

import { App } from "@/components/HomePage";

describe("Home map", () => {
  beforeEach(() => {
    fetchCityMeta.mockResolvedValue({
      city: "jakarta",
      transit_available: true,
      routing_mode: "mock",
      valhalla_reachable: false,
    });
    checkApiHealth.mockResolvedValue(true);
  });

  afterEach(() => {
    cleanup();
  });

  it("renders map shell", () => {
    render(<App />);
    expect(screen.getByTestId("map")).toBeTruthy();
  });

  it("disables compare until both pins set", () => {
    render(<App />);
    const compareBtn = screen.getByTestId("compare-button");
    expect(compareBtn.hasAttribute("disabled")).toBe(true);
  });

  it("renders map style toggle", () => {
    render(<App />);
    expect(screen.getByTestId("map-style-toggle")).toBeTruthy();
  });
});

describe("useCommutePins", () => {
  it("swap exchanges pin labels", async () => {
    const { useCommutePins } = await import("@/hooks/useCommutePins");
    const { renderHook, act: hookAct } = await import("@testing-library/react");
    const { result } = renderHook(() => useCommutePins());
    hookAct(() => {
      result.current.setPin("a", { lat: 1, lng: 2 });
      result.current.setPin("b", { lat: 3, lng: 4 });
    });
    hookAct(() => result.current.swapPins());
    expect(result.current.pins.a).toEqual({ lat: 3, lng: 4 });
    expect(result.current.pins.b).toEqual({ lat: 1, lng: 2 });
  });
});

describe("SearchBar debounce", () => {
  afterEach(() => cleanup());

  it("does not search before debounce", async () => {
    vi.useFakeTimers();
    const { searchGeocode } = await import("@/lib/api");
    const { LocationSearchInput } = await import(
      "@/components/geocode/LocationSearchInput"
    );
    render(<LocationSearchInput label="Dari" onSelect={() => {}} />);
    fireEvent.change(screen.getByLabelText("Dari"), {
      target: { value: "Monas" },
    });
    expect(searchGeocode).not.toHaveBeenCalled();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(299);
    });
    expect(searchGeocode).not.toHaveBeenCalled();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2);
    });
    expect(searchGeocode).toHaveBeenCalled();
    vi.useRealTimers();
  });

  it("dismisses suggestions on blur and selection", async () => {
    vi.useFakeTimers();
    const { fetchGeocodeCache } = await import("@/lib/supabase");
    const { LocationSearchInput } = await import(
      "@/components/geocode/LocationSearchInput"
    );
    const onSelect = vi.fn();

    vi.mocked(fetchGeocodeCache).mockResolvedValue([
      {
        lat: -6.17,
        lng: 106.82,
        display_name: "Monas, Jakarta",
      },
    ]);

    render(<LocationSearchInput label="Dari" onSelect={onSelect} />);
    const input = screen.getByLabelText("Dari");

    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "Monas" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(300);
    });
    expect(screen.getByText("Monas, Jakarta")).toBeTruthy();

    fireEvent.blur(input);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(150);
    });
    expect(screen.queryByText("Monas, Jakarta")).toBeNull();

    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "Monas " } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(300);
    });
    fireEvent.click(screen.getByText("Monas, Jakarta"));
    expect(onSelect).toHaveBeenCalled();
    expect(screen.queryByText("Monas, Jakarta")).toBeNull();

    vi.useRealTimers();
  });

  it("does not reopen suggestions when value matches committed label", async () => {
    vi.useFakeTimers();
    const { fetchGeocodeCache } = await import("@/lib/supabase");
    const { LocationSearchInput } = await import(
      "@/components/geocode/LocationSearchInput"
    );

    vi.mocked(fetchGeocodeCache).mockResolvedValue([
      {
        lat: -6.24,
        lng: 106.85,
        display_name: "-6.2454, 106.8572, Jakarta, Indonesia",
      },
    ]);

    const { rerender } = render(
      <LocationSearchInput
        label="Asal"
        value="-6.2454, 106.8572, Jakarta, Indonesia"
        onSelect={() => {}}
      />,
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(300);
    });
    expect(
      screen.queryByText("-6.2454, 106.8572, Jakarta, Indonesia"),
    ).toBeNull();

    rerender(
      <LocationSearchInput
        label="Asal"
        value="-6.2454, 106.8572, Jakarta, Indonesia"
        onSelect={() => {}}
      />,
    );
    await act(async () => {
      await vi.advanceTimersByTimeAsync(300);
    });
    expect(
      screen.queryByText("-6.2454, 106.8572, Jakarta, Indonesia"),
    ).toBeNull();

    vi.useRealTimers();
  });
});

describe("ComparisonCards", () => {
  afterEach(() => cleanup());

  it("shows fastest badge", async () => {
    const { ComparisonCards } = await import(
      "@/components/commute/ComparisonCards"
    );
    render(
      <ComparisonCards
        data={{
          fastest_mode: "transit",
          transit_available: true,
          results: [
            {
              mode: "transit",
              duration_min: 20,
              is_fastest: true,
              cost_idr: 3500,
              legs: [
                {
                  mode: "walk",
                  board_stop: "Asal",
                  alight_stop: "Halte",
                  duration_min: 5,
                },
                {
                  mode: "bus",
                  route_id: "TJ-1",
                  line_name: "Koridor 1",
                  board_stop: "Halte A",
                  alight_stop: "Halte B",
                  duration_min: 10,
                },
              ],
              route_polyline: [
                [106.82, -6.17],
                [106.84, -6.2],
              ],
            },
            {
              mode: "walking",
              duration_min: 40,
              is_fastest: false,
              cost_idr: 0,
            },
          ],
        }}
      />,
    );
    expect(screen.getByText("Paling cepat")).toBeTruthy();
    expect(screen.getByTestId("comparison-cards")).toBeTruthy();
    expect(screen.getByTestId("comparison-card-transit")).toBeTruthy();
  });

  it("shows car and motor cards in compare", async () => {
    const { ComparisonCards } = await import(
      "@/components/commute/ComparisonCards"
    );
    render(
      <ComparisonCards
        data={{
          fastest_mode: "motorcycle",
          transit_available: true,
          note: "Estimasi tanpa traffic real-time",
          results: [
            {
              mode: "car",
              duration_min: 25,
              is_fastest: false,
              distance_m: 12000,
            },
            {
              mode: "motorcycle",
              duration_min: 18,
              is_fastest: true,
              distance_m: 12000,
            },
          ],
        }}
      />,
    );
    expect(screen.getByTestId("comparison-card-car")).toBeTruthy();
    expect(screen.getByTestId("comparison-card-motorcycle")).toBeTruthy();
    expect(screen.getByText("Motor")).toBeTruthy();
  });

  it("expands transit legs and emits polyline", async () => {
    const onExpandMode = vi.fn();
    const { ComparisonCards } = await import(
      "@/components/commute/ComparisonCards"
    );
    render(
      <ComparisonCards
        onExpandMode={onExpandMode}
        data={{
          fastest_mode: "transit",
          transit_available: true,
          results: [
            {
              mode: "transit",
              duration_min: 20,
              is_fastest: true,
              legs: [
                { mode: "walk", board_stop: "Asal", duration_min: 5 },
                {
                  mode: "bus",
                  route_id: "TJ-1",
                  line_name: "Koridor 1",
                  duration_min: 10,
                },
              ],
              route_polyline: [
                [106.82, -6.17],
                [106.84, -6.2],
              ],
            },
          ],
        }}
      />,
    );
    fireEvent.click(screen.getByText("Lihat langkah transit"));
    expect(onExpandMode).toHaveBeenCalledWith("transit", [
      [106.82, -6.17],
      [106.84, -6.2],
    ]);
    expect(screen.getByText(/Koridor 1/)).toBeTruthy();
  });
});

describe("api unreachable banner", () => {
  afterEach(() => cleanup());

  it("shows banner when API health check fails", async () => {
    checkApiHealth.mockResolvedValue(false);
    render(<App />);
    expect(await screen.findByTestId("api-unreachable-banner")).toBeTruthy();
  });
});

describe("routing mock banner", () => {
  beforeEach(() => {
    checkApiHealth.mockResolvedValue(true);
  });

  afterEach(() => cleanup());

  it("hides banner when valhalla is reachable", async () => {
    fetchCityMeta.mockResolvedValueOnce({
      city: "jakarta",
      transit_available: true,
      routing_mode: "mock",
      valhalla_reachable: true,
    });
    render(<App />);
    await act(async () => {
      await Promise.resolve();
    });
    expect(screen.queryByTestId("routing-mock-banner")).toBeNull();
  });

  it("shows banner when mock and valhalla unreachable", async () => {
    fetchCityMeta.mockResolvedValueOnce({
      city: "jakarta",
      transit_available: true,
      routing_mode: "mock",
      valhalla_reachable: false,
    });
    render(<App />);
    expect(await screen.findByTestId("routing-mock-banner")).toBeTruthy();
  });
});

describe("transit unavailable banner", () => {
  afterEach(() => cleanup());

  it("shows banner when transit unavailable", async () => {
    fetchCityMeta.mockResolvedValueOnce({
      city: "bandung",
      transit_available: false,
      routing_mode: "mock",
      valhalla_reachable: false,
    });
    render(<App />);
    expect(
      await screen.findByTestId("transit-unavailable-banner"),
    ).toBeTruthy();
  });
});
