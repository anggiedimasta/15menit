from typing import Any

from app.models.schemas import (
    CommuteCompareRequest,
    CommuteCompareResponse,
    CommuteModeResult,
)
from app.services.routing import get_route
from app.services.transit import estimate_transit_fare, plan_transit_route


async def compare_commute(req: CommuteCompareRequest) -> CommuteCompareResponse:
    origin = req.origin
    dest = req.destination

    walk_d, walk_dist, _ = await get_route(
        origin.lat, origin.lng, dest.lat, dest.lng, "walking"
    )
    car_d, car_dist, _ = await get_route(
        origin.lat, origin.lng, dest.lat, dest.lng, "car"
    )
    motor_d, motor_dist, _ = await get_route(
        origin.lat, origin.lng, dest.lat, dest.lng, "motorcycle"
    )

    transit_plan = await plan_transit_route(
        origin.lat, origin.lng, dest.lat, dest.lng
    )
    cost, breakdown = estimate_transit_fare(transit_plan["fare_legs"])

    results: list[CommuteModeResult] = [
        CommuteModeResult(
            mode="walking",
            duration_min=walk_d,
            distance_m=walk_dist,
            cost_idr=0,
        ),
        CommuteModeResult(
            mode="transit",
            duration_min=transit_plan["duration_min"],
            transfers=transit_plan["transfers"],
            legs=transit_plan["legs"],
            route_polyline=transit_plan["polyline"],
            cost_idr=cost,
            fare_breakdown=breakdown,
        ),
        CommuteModeResult(
            mode="car",
            duration_min=car_d,
            distance_m=car_dist,
            cost_idr=None,
        ),
        CommuteModeResult(
            mode="motorcycle",
            duration_min=motor_d,
            distance_m=motor_dist,
            cost_idr=None,
        ),
    ]

    results.sort(key=lambda r: r.duration_min)
    fastest = results[0]
    second = results[1] if len(results) > 1 else None
    note = None
    if second and abs(fastest.duration_min - second.duration_min) < 5:
        note = "Selisih tipis"

    for r in results:
        r.is_fastest = r.mode == fastest.mode

    return CommuteCompareResponse(
        fastest_mode=fastest.mode,
        note=note,
        transit_available=True,
        results=results,
    )


def union_polygons(geometries: list[dict[str, Any]]) -> dict[str, Any]:
    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union

    if not geometries:
        return {"type": "Polygon", "coordinates": []}
    shapes = [shape(g) for g in geometries if g.get("coordinates")]
    merged = unary_union(shapes)
    return mapping(merged)


def coverage_score(kecamatan_id: str) -> dict[str, Any]:
    seed = sum(ord(c) for c in kecamatan_id) % 40
    return {
        "kecamatan_id": kecamatan_id,
        "coverage_pct": round(45.0 + seed, 1),
        "sample_count": 500,
    }
