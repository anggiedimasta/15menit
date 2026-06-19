import math
from typing import Any, Literal

import httpx
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep

from app.config import settings

Costing = Literal["pedestrian", "auto", "motorcycle"]
Mode = Literal["walking", "car", "motorcycle"]

WALK_SPEED_MPS = 5000 / 3600
CAR_SPEED_MPS = 25000 / 3600
MOTOR_SPEED_MPS = 30000 / 3600

# Simplified open-water masks (lng, lat) for mock isochrone clipping near Java coast.
_STATIC_WATER: tuple[Polygon, ...] = (
    Polygon(
        [
            (106.65, -6.095),
            (106.72, -6.088),
            (106.88, -6.07),
            (106.95, -6.0),
            (106.92, -5.52),
            (106.60, -5.55),
            (106.65, -6.095),
        ]
    ),
    Polygon(
        [
            (105.0, -5.52),
            (114.5, -5.52),
            (114.5, -5.48),
            (105.0, -5.48),
            (105.0, -5.52),
        ]
    ),
    Polygon(
        [
            (105.0, -8.85),
            (114.5, -8.85),
            (114.5, -8.35),
            (105.0, -8.35),
            (105.0, -8.85),
        ]
    ),
    Polygon(
        [
            (114.0, -8.85),
            (114.5, -8.85),
            (114.5, -5.5),
            (114.0, -5.5),
            (114.0, -8.85),
        ]
    ),
    Polygon(
        [
            (105.0, -8.85),
            (105.55, -8.85),
            (105.55, -5.5),
            (105.0, -5.5),
            (105.0, -8.85),
        ]
    ),
)


def _deterministic_noise(
    lat: float, lng: float, minutes: int, mode: str, index: int
) -> float:
    """Irregularity factor ~0.72–1.18, stable for same inputs."""
    seed = hash((round(lat, 5), round(lng, 5), minutes, mode, index)) & 0xFFFFFFFF
    return 0.72 + (seed % 460) / 1000.0


def _meters_to_lat_lng_offset(
    lat: float, meters: float, angle_rad: float
) -> tuple[float, float]:
    dlat = (meters * math.sin(angle_rad)) / 111_320
    dlng = (meters * math.cos(angle_rad)) / (
        111_320 * max(math.cos(math.radians(lat)), 0.2)
    )
    return dlat, dlng


def _water_mask_for_point(lat: float, lng: float, radius_m: float) -> Any | None:
    """Prepared union of static water polygons intersecting the reach area."""
    origin = Point(lng, lat)
    search = origin.buffer((radius_m / 111_320) * 1.25)
    nearby = [poly for poly in _STATIC_WATER if poly.intersects(search)]
    if not nearby:
        return None
    return prep(unary_union(nearby))


def _clip_radius_to_land(
    lat: float,
    lng: float,
    angle_rad: float,
    max_radius_m: float,
    water: Any,
    *,
    step_m: float = 40.0,
) -> float:
    """Shrink a ray until its endpoint is not inside open water."""
    dlat, dlng = _meters_to_lat_lng_offset(lat, max_radius_m, angle_rad)
    if not water.contains(Point(lng + dlng, lat + dlat)):
        return max_radius_m

    lo, hi = 0.0, max_radius_m
    while hi - lo > step_m:
        mid = (lo + hi) / 2
        dlat, dlng = _meters_to_lat_lng_offset(lat, mid, angle_rad)
        if water.contains(Point(lng + dlng, lat + dlat)):
            hi = mid
        else:
            lo = mid
    return lo


def mock_isochrone_polygon(
    lat: float,
    lng: float,
    minutes: int,
    mode: Mode = "walking",
    *,
    water: Any | None = None,
) -> dict[str, Any]:
    """Street-grid-ish walk reach polygon — intentionally not a perfect circle."""
    speed = {
        "walking": WALK_SPEED_MPS,
        "car": CAR_SPEED_MPS,
        "motorcycle": MOTOR_SPEED_MPS,
    }[mode]
    base_radius_m = speed * minutes * 60
    if water is None:
        water = _water_mask_for_point(lat, lng, base_radius_m)
    num_points = 36
    points: list[list[float]] = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        # Cardinal corridors reach further (grid-aligned streets).
        street_factor = 0.82 + 0.18 * (
            abs(math.cos(2 * angle)) + abs(math.sin(2 * angle))
        )
        noise = _deterministic_noise(lat, lng, minutes, mode, i)
        diagonal_pinch = 0.88 + 0.12 * max(
            abs(math.cos(angle)), abs(math.sin(angle))
        )
        radius_m = base_radius_m * street_factor * noise * diagonal_pinch
        if water is not None:
            radius_m = _clip_radius_to_land(lat, lng, angle, radius_m, water)
        dlat, dlng = _meters_to_lat_lng_offset(lat, radius_m, angle)
        points.append([lng + dlng, lat + dlat])
    points.append(points[0])
    return {"type": "Polygon", "coordinates": [points]}


def mock_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    mode: Mode = "walking",
) -> tuple[int, int, list[list[float]]]:
    speed = {
        "walking": WALK_SPEED_MPS,
        "car": CAR_SPEED_MPS,
        "motorcycle": MOTOR_SPEED_MPS,
    }[mode]
    dlat = dest_lat - origin_lat
    dlng = dest_lng - origin_lng
    distance_m = int(
        math.hypot(dlat * 111_320, dlng * 111_320 * math.cos(math.radians(origin_lat)))
    )
    duration_min = max(1, int(distance_m / speed / 60))
    polyline = [[origin_lng, origin_lat], [dest_lng, dest_lat]]
    return duration_min, distance_m, polyline


async def valhalla_isochrone(
    lat: float, lng: float, minutes: int, costing: Costing
) -> dict[str, Any]:
    payload = {
        "locations": [{"lat": lat, "lon": lng}],
        "costing": costing,
        "contours": [{"time": minutes}],
        "polygons": True,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{settings.valhalla_url}/isochrone", json=payload
        )
        response.raise_for_status()
        data = response.json()
        if data.get("type") == "FeatureCollection":
            return data["features"][0]["geometry"]
        return data["features"][0]["geometry"]


async def valhalla_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    costing: Costing,
) -> tuple[int, int, list[list[float]]]:
    payload = {
        "locations": [
            {"lat": origin_lat, "lon": origin_lng},
            {"lat": dest_lat, "lon": dest_lng},
        ],
        "costing": costing,
        "units": "kilometers",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{settings.valhalla_url}/route", json=payload)
        response.raise_for_status()
        trip = response.json()["trip"]
        summary = trip["summary"]
        duration_min = max(1, int(summary["time"] / 60))
        distance_m = int(summary["length"] * 1000)
        shape = trip["legs"][0]["shape"]
        polyline = _decode_polyline(shape)
        return duration_min, distance_m, polyline


def _decode_polyline(encoded: str) -> list[list[float]]:
    """Decode Valhalla encoded polyline to [lng, lat] pairs."""
    index = 0
    lat = 0
    lng = 0
    coordinates: list[list[float]] = []
    while index < len(encoded):
        for _ in range(2):
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if _ == 0:
                lat += delta
            else:
                lng += delta
        coordinates.append([lng / 1e6, lat / 1e6])
    return coordinates


async def get_isochrone(
    lat: float, lng: float, minutes: int, mode: Mode = "walking"
) -> tuple[dict[str, Any], str]:
    costing_map: dict[Mode, Costing] = {
        "walking": "pedestrian",
        "car": "auto",
        "motorcycle": "motorcycle",
    }
    if settings.routing_mode == "mock":
        return mock_isochrone_polygon(lat, lng, minutes, mode), "mock"
    try:
        geometry = await valhalla_isochrone(
            lat, lng, minutes, costing_map[mode]
        )
        return geometry, "valhalla"
    except (httpx.HTTPError, KeyError, IndexError):
        return mock_isochrone_polygon(lat, lng, minutes, mode), "mock"


async def get_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    mode: Mode = "walking",
) -> tuple[int, int, list[list[float]]]:
    costing_map: dict[Mode, Costing] = {
        "walking": "pedestrian",
        "car": "auto",
        "motorcycle": "motorcycle",
    }
    if settings.routing_mode == "mock":
        return mock_route(origin_lat, origin_lng, dest_lat, dest_lng, mode)
    try:
        return await valhalla_route(
            origin_lat, origin_lng, dest_lat, dest_lng, costing_map[mode]
        )
    except (httpx.HTTPError, KeyError, IndexError):
        return mock_route(origin_lat, origin_lng, dest_lat, dest_lng, mode)
