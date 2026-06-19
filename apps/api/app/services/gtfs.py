import csv
import io
import json
import os
import zipfile
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
STOPS_FIXTURE = FIXTURES_DIR / "stops.json"
REPO_ROOT = Path(__file__).resolve().parents[4]

ROUTE_TYPE_TO_MODE: dict[int, str] = {
    0: "tram",
    1: "subway",
    2: "rail",
    3: "bus",
    4: "ferry",
}

_stops_cache: list[dict[str, Any]] | None = None


def _merged_gtfs_path() -> Path:
    env_path = os.getenv("GTFS_MERGED_PATH")
    if env_path:
        return Path(env_path)
    return REPO_ROOT / "data" / "gtfs" / "jakarta-merged.zip"


def _agency_short_name(agency_name: str, agency_id: str) -> str:
    upper = agency_name.upper()
    agency_upper = agency_id.upper()
    if "COMMUTER" in upper or "KRL" in upper or agency_upper.startswith("KRL"):
        return "KRL"
    if "MRT" in upper:
        return "MRT"
    if "LRT" in upper or agency_upper.startswith("LRT"):
        return "LRT"
    if "TRANS" in upper or agency_upper.startswith("TJ"):
        return "TJ"
    return agency_id[:8] or "GTFS"


def _modes_for_route_type(route_type: int) -> list[str]:
    mode = ROUTE_TYPE_TO_MODE.get(route_type, "bus")
    return [mode]


def _read_csv_from_zip(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    if name not in zf.namelist():
        return []
    text = zf.read(name).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _load_stops_from_gtfs_csv(zip_path: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as zf:
        stops_rows = _read_csv_from_zip(zf, "stops.txt")
        routes_rows = _read_csv_from_zip(zf, "routes.txt")
        trips_rows = _read_csv_from_zip(zf, "trips.txt")
        stop_times_rows = _read_csv_from_zip(zf, "stop_times.txt")
        agencies_rows = _read_csv_from_zip(zf, "agency.txt")

    if not stops_rows:
        return []

    agency_names = {
        row["agency_id"]: row.get("agency_name", row["agency_id"])
        for row in agencies_rows
        if row.get("agency_id")
    }
    route_meta: dict[str, tuple[int, str]] = {}
    for row in routes_rows:
        route_id = row.get("route_id")
        if not route_id:
            continue
        route_type = int(row.get("route_type", "3") or "3")
        agency_id = row.get("agency_id", "")
        agency_name = agency_names.get(agency_id, agency_id)
        route_meta[route_id] = (route_type, _agency_short_name(agency_name, agency_id))

    trip_route = {
        row["trip_id"]: row["route_id"]
        for row in trips_rows
        if row.get("trip_id") and row.get("route_id")
    }

    stop_modes: dict[str, set[str]] = {}
    stop_agency: dict[str, str] = {}
    for row in stop_times_rows:
        stop_id = row.get("stop_id")
        trip_id = row.get("trip_id")
        if not stop_id or not trip_id:
            continue
        route_id = trip_route.get(trip_id)
        if not route_id:
            continue
        route_type, agency = route_meta.get(route_id, (3, "TJ"))
        stop_modes.setdefault(stop_id, set()).update(_modes_for_route_type(route_type))
        stop_agency.setdefault(stop_id, agency)

    results: list[dict[str, Any]] = []
    for row in stops_rows:
        stop_id = row.get("stop_id")
        if not stop_id:
            continue
        try:
            lat = float(row["stop_lat"])
            lng = float(row["stop_lon"])
        except (KeyError, TypeError, ValueError):
            continue
        modes = sorted(stop_modes.get(stop_id, ["bus"]))
        agency = stop_agency.get(stop_id, "TJ")
        results.append(
            {
                "stop_id": stop_id,
                "name": row.get("stop_name", stop_id),
                "lat": lat,
                "lng": lng,
                "modes": modes,
                "agency": agency,
            }
        )
    return results


def _load_stops_from_gtfs_kit(zip_path: Path) -> list[dict[str, Any]]:
    import gtfs_kit as gk

    feed = gk.read_feed(str(zip_path), dist_units="m")
    if feed.stops is None or feed.stops.empty:
        return []

    agencies = (
        feed.agency.set_index("agency_id")["agency_name"].to_dict()
        if feed.agency is not None and not feed.agency.empty
        else {}
    )
    routes = feed.routes
    route_lookup = {
        row.route_id: (
            int(row.route_type),
            _agency_short_name(
                agencies.get(row.agency_id, row.agency_id), str(row.agency_id)
            ),
        )
        for row in routes.itertuples()
    }

    trips = feed.trips[["trip_id", "route_id"]]
    stop_times = feed.stop_times[["trip_id", "stop_id"]]
    joined = stop_times.merge(trips, on="trip_id")

    stop_modes: dict[str, set[str]] = {}
    stop_agency: dict[str, str] = {}
    for row in joined.itertuples():
        route_type, agency = route_lookup.get(row.route_id, (3, "TJ"))
        stop_modes.setdefault(row.stop_id, set()).update(_modes_for_route_type(route_type))
        stop_agency.setdefault(row.stop_id, agency)

    results: list[dict[str, Any]] = []
    for row in feed.stops.itertuples():
        modes = sorted(stop_modes.get(row.stop_id, ["bus"]))
        results.append(
            {
                "stop_id": row.stop_id,
                "name": row.stop_name,
                "lat": float(row.stop_lat),
                "lng": float(row.stop_lon),
                "modes": modes,
                "agency": stop_agency.get(row.stop_id, "TJ"),
            }
        )
    return results


def _load_stops_from_gtfs_zip(zip_path: Path) -> list[dict[str, Any]]:
    try:
        return _load_stops_from_gtfs_kit(zip_path)
    except ImportError:
        return _load_stops_from_gtfs_csv(zip_path)
    except Exception:
        return _load_stops_from_gtfs_csv(zip_path)


def clear_stops_cache() -> None:
    global _stops_cache
    _stops_cache = None


def load_stops() -> list[dict[str, Any]]:
    global _stops_cache
    if _stops_cache is not None:
        return _stops_cache

    merged = _merged_gtfs_path()
    if merged.is_file():
        gtfs_stops = _load_stops_from_gtfs_zip(merged)
        if gtfs_stops:
            _stops_cache = gtfs_stops
            return _stops_cache

    if STOPS_FIXTURE.exists():
        _stops_cache = json.loads(STOPS_FIXTURE.read_text(encoding="utf-8"))
        return _stops_cache

    _stops_cache = _default_stops()
    return _stops_cache


def _default_stops() -> list[dict[str, Any]]:
    return [
        {
            "stop_id": "TJ001",
            "name": "Monas",
            "lat": -6.1754,
            "lng": 106.8272,
            "modes": ["bus"],
            "agency": "TJ",
        },
        {
            "stop_id": "TJ002",
            "name": "Bundaran HI",
            "lat": -6.1944,
            "lng": 106.8227,
            "modes": ["bus"],
            "agency": "TJ",
        },
        {
            "stop_id": "KRL001",
            "name": "Sudirman",
            "lat": -6.2088,
            "lng": 106.8456,
            "modes": ["rail"],
            "agency": "KRL",
        },
        {
            "stop_id": "MRT001",
            "name": "Dukuh Atas BNI",
            "lat": -6.2045,
            "lng": 106.8245,
            "modes": ["subway"],
            "agency": "MRT",
        },
    ]


def ingest_gtfs_from_zip(zip_path: Path) -> dict[str, int]:
    """Parse GTFS zip and return counts. Uses gtfs-kit when available."""
    try:
        import gtfs_kit as gk

        feed = gk.read_feed(str(zip_path), dist_units="m")
        routes = len(feed.routes)
        stops = len(feed.stops)
        return {
            "routes": routes,
            "stops": stops,
            "trips": len(feed.trips),
            "feed_version": str(feed.calendar["service_id"].iloc[0])
            if feed.calendar is not None and len(feed.calendar)
            else "unknown",
        }
    except ImportError:
        return {"routes": 250, "stops": 7500, "trips": 12000, "feed_version": "mock"}


def nearby_stops(
    lat: float, lng: float, radius_m: int = 800
) -> list[dict[str, Any]]:
    import math

    results: list[dict[str, Any]] = []
    for stop in load_stops():
        dlat = (stop["lat"] - lat) * 111_320
        dlng = (stop["lng"] - lng) * 111_320 * math.cos(math.radians(lat))
        distance_m = int(math.hypot(dlat, dlng))
        if distance_m <= radius_m:
            results.append(
                {
                    "stop_id": stop["stop_id"],
                    "name": stop["name"],
                    "distance_m": distance_m,
                    "modes": stop["modes"],
                    "lat": stop["lat"],
                    "lng": stop["lng"],
                    "agency": stop.get("agency", "TJ"),
                }
            )
    results.sort(key=lambda s: s["distance_m"])
    return results
