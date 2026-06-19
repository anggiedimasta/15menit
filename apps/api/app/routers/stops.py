from fastapi import APIRouter, HTTPException

from app.core.bbox import in_java_bbox
from app.models.schemas import MultiOriginRequest, NearbyStopsRequest, StopInfo
from app.services.commute import union_polygons
from app.services.gtfs import nearby_stops
from app.services.routing import get_isochrone

router = APIRouter(prefix="/stops", tags=["stops"])


@router.post("/nearby", response_model=list[StopInfo])
async def stops_nearby(body: NearbyStopsRequest) -> list[StopInfo]:
    if not in_java_bbox(body.lat, body.lng):
        raise HTTPException(status_code=400, detail="Point outside service area")
    raw = nearby_stops(body.lat, body.lng, body.radius_m)
    return [
        StopInfo(
            stop_id=s["stop_id"],
            name=s["name"],
            distance_m=s["distance_m"],
            modes=s["modes"],
        )
        for s in raw
    ]


@router.post("/multi-origin-isochrone")
async def multi_origin_isochrone(body: MultiOriginRequest) -> dict:
    if not in_java_bbox(body.lat, body.lng):
        raise HTTPException(status_code=400, detail="Point outside service area")

    stops = nearby_stops(body.lat, body.lng, radius_m=1000)[: body.max_origins]
    origins = [{"lat": body.lat, "lng": body.lng, "name": "Home"}] + [
        {"lat": s["lat"], "lng": s["lng"], "name": s["name"]} for s in stops
    ]

    geometries = []
    for origin in origins:
        geom = await get_isochrone(origin["lat"], origin["lng"], body.minutes, "walking")
        geometries.append(geom)

    merged = union_polygons(geometries)
    return {
        "type": "Feature",
        "geometry": merged,
        "properties": {
            "origin_count": len(origins),
            "stop_count": len(stops),
            "minutes": body.minutes,
        },
    }
