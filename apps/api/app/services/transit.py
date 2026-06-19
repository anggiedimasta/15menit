import csv
import io
import json
import math
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.schemas import TransitLeg
from app.services.gtfs import _merged_gtfs_path, nearby_stops
from app.services.routing import get_isochrone, get_route, mock_isochrone_polygon

FARES_PATH = Path(__file__).resolve().parents[3] / "data" / "fares" / "jakarta.json"
REPO_ROOT = Path(__file__).resolve().parents[4]

WALK_SPEED_MPS = 5000 / 3600
BUS_SPEED_MPS = 20000 / 3600
RAIL_SPEED_MPS = 35000 / 3600

DEFAULT_LINE_NAMES = {
    "TJ": "TransJakarta",
    "KRL": "KRL Commuter Line",
    "MRT": "MRT Jakarta",
    "LRT": "LRT Jakarta",
    "LRT-JKT": "LRT Jakarta",
    "LRT-JBD": "LRT Jabodebek",
}


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _walk_minutes(distance_m: float) -> int:
    return max(1, int(distance_m / WALK_SPEED_MPS / 60))


def _transit_speed(mode: str) -> float:
    if mode in ("rail", "subway", "tram"):
        return RAIL_SPEED_MPS
    return BUS_SPEED_MPS


def _mode_label(stop_modes: list[str]) -> str:
    if "rail" in stop_modes:
        return "rail"
    if "subway" in stop_modes:
        return "subway"
    if "tram" in stop_modes:
        return "tram"
    return "bus"


def _agency_from_gtfs_stop_id(stop_id: str) -> str | None:
    upper = stop_id.upper()
    if "TRANSJAKARTA" in upper:
        return "TJ"
    for tag in ("KRL", "MRT", "LRT"):
        if tag in upper:
            return tag
    if upper.startswith("TJ_") or "_TJ_" in upper:
        return "TJ"
    return None


def _default_line_name(agency: str, route_id: str | None = None) -> str:
    if route_id:
        upper_route = route_id.upper()
        if "LRT-JBD" in upper_route or "JABODEBEK" in upper_route:
            return DEFAULT_LINE_NAMES["LRT-JBD"]
        if "LRT-JKT" in upper_route:
            return DEFAULT_LINE_NAMES["LRT-JKT"]
    return DEFAULT_LINE_NAMES.get(agency.upper(), agency)


def _parse_gtfs_time(value: str) -> int:
    parts = value.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2]) if len(parts) > 2 else 0
    return hours * 3600 + minutes * 60 + seconds


@dataclass(frozen=True)
class MergedGtfsFeed:
    stops: list[dict[str, str]]
    stop_times: list[dict[str, str]]
    trips: list[dict[str, str]]
    routes: list[dict[str, str]]


def _read_gtfs_csv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    if name not in zf.namelist():
        return []
    text = zf.read(name).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


@lru_cache(maxsize=1)
def _load_merged_feed() -> MergedGtfsFeed | None:
    merged_path = _merged_gtfs_path()
    if not merged_path.exists():
        return None
    try:
        with zipfile.ZipFile(merged_path) as zf:
            return MergedGtfsFeed(
                stops=_read_gtfs_csv(zf, "stops.txt"),
                stop_times=_read_gtfs_csv(zf, "stop_times.txt"),
                trips=_read_gtfs_csv(zf, "trips.txt"),
                routes=_read_gtfs_csv(zf, "routes.txt"),
            )
    except Exception:
        return None


def _lookup_route_line_name(feed: MergedGtfsFeed, route_id: str) -> str | None:
    for row in feed.routes:
        if row.get("route_id") == route_id:
            return (
                row.get("route_long_name")
                or row.get("route_short_name")
                or None
            )
    return None


def _line_name_for_stop(feed: MergedGtfsFeed, stop_id: str) -> str | None:
    trip_ids = {
        row["trip_id"]
        for row in feed.stop_times
        if row.get("stop_id") == stop_id
    }
    if not trip_ids:
        return None
    trips_by_id = {row["trip_id"]: row for row in feed.trips}
    routes_by_id = {row["route_id"]: row for row in feed.routes}
    for trip_id in trip_ids:
        route_id = trips_by_id.get(trip_id, {}).get("route_id")
        if not route_id:
            continue
        route = routes_by_id.get(route_id, {})
        name = route.get("route_long_name") or route.get("route_short_name")
        if name:
            return name
    return None


def _match_gtfs_stop_id(
    feed: MergedGtfsFeed, lat: float, lng: float, radius_m: float = 250
) -> str | None:
    best_id: str | None = None
    best_dist = radius_m
    for row in feed.stops:
        dist = _haversine_m(lat, lng, float(row["stop_lat"]), float(row["stop_lon"]))
        if dist < best_dist:
            best_dist = dist
            best_id = row["stop_id"]
    return best_id


def _gtfs_trip_duration_min(board_id: str, alight_id: str) -> tuple[int, str, str] | None:
    feed = _load_merged_feed()
    if feed is None or not feed.stop_times:
        return None

    board_trip_ids = {
        row["trip_id"]
        for row in feed.stop_times
        if row.get("stop_id") == board_id
    }
    if not board_trip_ids:
        return None

    trips_by_id = {row["trip_id"]: row for row in feed.trips}
    routes_by_id = {row["route_id"]: row for row in feed.routes}
    times_by_trip: dict[str, list[dict[str, str]]] = {}
    for row in feed.stop_times:
        times_by_trip.setdefault(row["trip_id"], []).append(row)

    best: tuple[int, str, str] | None = None
    for trip_id in board_trip_ids:
        ordered = sorted(
            times_by_trip.get(trip_id, []),
            key=lambda row: int(row.get("stop_sequence", 0)),
        )
        stop_ids = [row["stop_id"] for row in ordered]
        if board_id not in stop_ids or alight_id not in stop_ids:
            continue
        if stop_ids.index(alight_id) <= stop_ids.index(board_id):
            continue
        board_row = next(row for row in ordered if row["stop_id"] == board_id)
        alight_row = next(row for row in ordered if row["stop_id"] == alight_id)
        seconds = _parse_gtfs_time(alight_row["arrival_time"]) - _parse_gtfs_time(
            board_row["departure_time"]
        )
        minutes = max(1, seconds // 60)
        trip_row = trips_by_id.get(trip_id, {})
        route_id = trip_row.get("route_id", trip_id)
        route_row = routes_by_id.get(route_id, {})
        line_name = (
            route_row.get("route_long_name")
            or route_row.get("route_short_name")
            or route_id
        )
        if best is None or minutes < best[0]:
            best = (minutes, route_id, line_name)
    return best


def _next_weekday_0730_wib() -> str:
    now = datetime.now(UTC) + timedelta(hours=7)
    days_ahead = (0 - now.weekday()) % 7
    if days_ahead == 0 and now.hour >= 8:
        days_ahead = 7
    departure = (now + timedelta(days=days_ahead)).replace(
        hour=7, minute=30, second=0, microsecond=0
    )
    return departure.isoformat()


def _polygon_area(geometry: dict[str, Any]) -> float:
    from shapely.geometry import shape

    return shape(geometry).area


async def transit_isochrone(
    lat: float, lng: float, minutes: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = {
        "modes_used": ["WALK", "TRANSIT"],
        "departure_time": _next_weekday_0730_wib(),
    }
    if settings.transit_mode == "mock":
        walk = mock_isochrone_polygon(lat, lng, minutes, "walking")
        transit = mock_isochrone_polygon(
            lat, lng, int(minutes * 1.35), "walking"
        )
        metadata["walk_area_ratio"] = round(
            _polygon_area(transit) / max(_polygon_area(walk), 1e-12), 2
        )
        return transit, metadata

    try:
        import r5py  # type: ignore[import-untyped]

        osm_path = REPO_ROOT / "data" / "osm" / "java-latest.osm.pbf"
        gtfs_path = settings.gtfs_merged_path
        if not osm_path.exists() or not gtfs_path.exists():
            raise FileNotFoundError("r5 network files missing")
        transport = r5py.TransportNetwork(str(osm_path), [str(gtfs_path)])
        iso = r5py.Isochrones(
            transport,
            origins=[(lat, lng)],
            departure=_next_weekday_0730_wib(),
            transport_modes=["WALK", "TRANSIT"],
            max_time=timedelta(minutes=minutes),
        )
        geometry = json.loads(iso.to_json())["features"][0]["geometry"]
        return geometry, metadata
    except Exception:
        walk_geom = await get_isochrone(lat, lng, minutes, "walking")
        expanded = mock_isochrone_polygon(
            lat, lng, int(minutes * 1.25), "walking"
        )
        metadata["fallback"] = "r5py unavailable — expanded walk estimate"
        return expanded or walk_geom, metadata


def _mock_transit_plan(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> dict[str, Any]:
    origin_stops = nearby_stops(origin_lat, origin_lng, radius_m=1000)
    dest_stops = nearby_stops(dest_lat, dest_lng, radius_m=1000)
    feed = _load_merged_feed()
    stop_limit = 8 if feed is not None and feed.stop_times else 5

    direct_walk_m = _haversine_m(origin_lat, origin_lng, dest_lat, dest_lng)
    best: dict[str, Any] | None = None

    if not origin_stops or not dest_stops:
        walk_d = _walk_minutes(direct_walk_m)
        return {
            "duration_min": walk_d,
            "transfers": 0,
            "legs": [
                TransitLeg(
                    mode="walk",
                    duration_min=walk_d,
                    board_stop="Asal",
                    alight_stop="Tujuan",
                )
            ],
            "polyline": [
                [origin_lng, origin_lat],
                [dest_lng, dest_lat],
            ],
            "fare_legs": [],
        }

    for board in origin_stops[:stop_limit]:
        for alight in dest_stops[:stop_limit]:
            if board["stop_id"] == alight["stop_id"]:
                continue
            walk_to = _haversine_m(
                origin_lat, origin_lng, board["lat"], board["lng"]
            )
            walk_from = _haversine_m(
                alight["lat"], alight["lng"], dest_lat, dest_lng
            )
            transit_m = _haversine_m(
                board["lat"], board["lng"], alight["lat"], alight["lng"]
            )
            mode = _mode_label(board["modes"])
            transit_min = max(
                3, int(transit_m / _transit_speed(mode) / 60)
            )
            agency = board.get("agency", "TJ")
            route_id = f"{agency}-{board['stop_id']}"
            line_name: str | None = None
            gtfs_timed = False
            if feed is not None:
                board_gtfs = _match_gtfs_stop_id(
                    feed, board["lat"], board["lng"]
                )
                alight_gtfs = _match_gtfs_stop_id(
                    feed, alight["lat"], alight["lng"]
                )
                if board_gtfs:
                    gtfs_agency = _agency_from_gtfs_stop_id(board_gtfs)
                    if gtfs_agency:
                        agency = gtfs_agency
                        route_id = f"{agency}-{board_gtfs.split('_')[-1]}"
                if board_gtfs and alight_gtfs:
                    gtfs_trip = _gtfs_trip_duration_min(board_gtfs, alight_gtfs)
                    if gtfs_trip is not None:
                        transit_min, route_id, line_name = gtfs_trip
                        gtfs_timed = True
                    else:
                        line_name = _line_name_for_stop(feed, board_gtfs)
                        if line_name is None:
                            line_name = _lookup_route_line_name(feed, route_id)
                elif board_gtfs:
                    line_name = _line_name_for_stop(feed, board_gtfs)
            if line_name is None:
                line_name = _default_line_name(agency, route_id)
            total = (
                _walk_minutes(walk_to)
                + transit_min
                + _walk_minutes(walk_from)
            )
            candidate = {
                "duration_min": total,
                "transfers": 0,
                "board": board,
                "alight": alight,
                "mode": mode,
                "walk_to_min": _walk_minutes(walk_to),
                "transit_min": transit_min,
                "walk_from_min": _walk_minutes(walk_from),
                "route_id": route_id,
                "line_name": line_name,
                "agency": agency,
                "gtfs_timed": gtfs_timed,
            }
            if best is None or candidate["duration_min"] < best["duration_min"]:
                best = candidate

    if best is None:
        walk_d = _walk_minutes(direct_walk_m)
        return {
            "duration_min": walk_d,
            "transfers": 0,
            "legs": [
                TransitLeg(mode="walk", duration_min=walk_d, board_stop="Asal")
            ],
            "polyline": [[origin_lng, origin_lat], [dest_lng, dest_lat]],
            "fare_legs": [],
        }

    board = best["board"]
    alight = best["alight"]
    agency = best.get("agency") or board.get("agency", "TJ")
    route_id = best.get("route_id") or f"{agency}-{board['stop_id']}"
    line_name = best.get("line_name") or _default_line_name(agency, route_id)
    legs = [
        TransitLeg(
            mode="walk",
            duration_min=best["walk_to_min"],
            board_stop="Asal",
            alight_stop=board["name"],
        ),
        TransitLeg(
            mode=best["mode"],
            route_id=route_id,
            line_name=line_name,
            board_stop=board["name"],
            alight_stop=alight["name"],
            duration_min=best["transit_min"],
        ),
        TransitLeg(
            mode="walk",
            duration_min=best["walk_from_min"],
            board_stop=alight["name"],
            alight_stop="Tujuan",
        ),
    ]
    polyline = [
        [origin_lng, origin_lat],
        [board["lng"], board["lat"]],
        [alight["lng"], alight["lat"]],
        [dest_lng, dest_lat],
    ]
    fare_legs = [{"agency": agency}]
    if agency == "KRL":
        fare_legs[0]["station_pair"] = f"{board['name']}-{alight['name']}"

    result = {
        "duration_min": best["duration_min"],
        "transfers": 0,
        "legs": legs,
        "polyline": polyline,
        "fare_legs": fare_legs,
    }
    if best.get("gtfs_timed"):
        result["source"] = "gtfs"
    return result


async def _r5_transit_duration(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> int | None:
    try:
        import r5py  # type: ignore[import-untyped]

        osm_path = REPO_ROOT / "data" / "osm" / "java-latest.osm.pbf"
        gtfs_path = settings.gtfs_merged_path
        if not osm_path.exists() or not gtfs_path.exists():
            return None
        transport = r5py.TransportNetwork(str(osm_path), [str(gtfs_path)])
        matrix = r5py.TravelTimeMatrix(
            transport,
            origins=[(origin_lat, origin_lng)],
            destinations=[(dest_lat, dest_lng)],
            departure=_next_weekday_0730_wib(),
            transport_modes=["WALK", "TRANSIT"],
        )
        seconds = int(matrix["travel_time"].iloc[0])
        return max(1, seconds // 60)
    except Exception:
        return None


async def plan_transit_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> dict[str, Any]:
    mock_plan = _mock_transit_plan(origin_lat, origin_lng, dest_lat, dest_lng)

    if settings.transit_mode == "r5":
        r5_min = await _r5_transit_duration(
            origin_lat, origin_lng, dest_lat, dest_lng
        )
        if r5_min is not None:
            mock_plan["duration_min"] = r5_min
            mock_plan["source"] = "r5py"

    return mock_plan


def load_fare_tables() -> dict[str, Any]:
    if FARES_PATH.exists():
        return json.loads(FARES_PATH.read_text(encoding="utf-8"))
    return {
        "transjakarta_flat": 3500,
        "krl": {"Manggarai-Sudirman": 5000},
        "mrt_per_segment": 5000,
    }


def estimate_transit_fare(legs: list[dict[str, Any]]) -> tuple[int | None, list[dict[str, Any]]]:
    tables = load_fare_tables()
    breakdown: list[dict[str, Any]] = []
    total = 0
    unknown = False
    for leg in legs:
        agency = leg.get("agency", "").upper()
        if agency in ("TJ", "TRANSJAKARTA"):
            fare = tables.get("transjakarta_flat", 3500)
            breakdown.append({"agency": "TransJakarta", "fare_idr": fare})
            total += fare
        elif agency == "KRL":
            pair = leg.get("station_pair")
            krl_table = tables.get("krl", {})
            fare = krl_table.get(pair) if pair else None
            if fare is None:
                unknown = True
            else:
                breakdown.append({"agency": "KRL", "fare_idr": fare})
                total += fare
        elif agency == "MRT":
            segments = leg.get("segments", 1)
            fare = tables.get("mrt_per_segment", 5000) * segments
            breakdown.append({"agency": "MRT", "fare_idr": fare})
            total += fare
        else:
            unknown = True
    if unknown and not breakdown:
        return None, breakdown
    return total if not unknown or breakdown else total, breakdown
