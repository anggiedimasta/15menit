from fastapi import APIRouter, HTTPException

from app.core.bbox import in_java_bbox
from app.core.cache import isochrone_cache
from app.models.schemas import IsochroneRequest, IsochroneResponse
from app.services.routing import get_isochrone
from app.services.transit import transit_isochrone

router = APIRouter(prefix="/isochrone", tags=["isochrone"])


def _build_response(
    geometry: dict, lat: float, lng: float, minutes: int, mode: str, cached: bool
) -> IsochroneResponse:
    return IsochroneResponse(
        geometry=geometry,
        properties={
            "lat": lat,
            "lng": lng,
            "minutes": minutes,
            "mode": mode,
            "cached": cached,
        },
    )


@router.post("/walk", response_model=IsochroneResponse)
async def walk_isochrone(body: IsochroneRequest) -> IsochroneResponse:
    if not in_java_bbox(body.lat, body.lng):
        raise HTTPException(status_code=400, detail="Point outside Java service area")

    cache_key = {"lat": body.lat, "lng": body.lng, "minutes": body.minutes, "mode": "walk"}
    cached = isochrone_cache.get("isochrone", cache_key)
    if cached:
        return _build_response(cached, body.lat, body.lng, body.minutes, "walking", True)

    geometry = await get_isochrone(body.lat, body.lng, body.minutes, "walking")
    isochrone_cache.set("isochrone", cache_key, geometry)
    return _build_response(geometry, body.lat, body.lng, body.minutes, "walking", False)


@router.post("/car", response_model=IsochroneResponse)
async def car_isochrone(body: IsochroneRequest) -> IsochroneResponse:
    if not in_java_bbox(body.lat, body.lng):
        raise HTTPException(status_code=400, detail="Point outside Java service area")

    cache_key = {"lat": body.lat, "lng": body.lng, "minutes": body.minutes, "mode": "car"}
    cached = isochrone_cache.get("isochrone", cache_key)
    if cached:
        return _build_response(cached, body.lat, body.lng, body.minutes, "car", True)

    geometry = await get_isochrone(body.lat, body.lng, body.minutes, "car")
    isochrone_cache.set("isochrone", cache_key, geometry)
    return _build_response(
        geometry, body.lat, body.lng, body.minutes, "car", False
    )


@router.post("/transit", response_model=IsochroneResponse)
async def transit_isochrone_endpoint(body: IsochroneRequest) -> IsochroneResponse:
    if not in_java_bbox(body.lat, body.lng):
        raise HTTPException(status_code=400, detail="Point outside Java service area")

    geometry, metadata = await transit_isochrone(body.lat, body.lng, body.minutes)
    return IsochroneResponse(
        geometry=geometry,
        properties={
            "lat": body.lat,
            "lng": body.lng,
            "minutes": body.minutes,
            "mode": "transit",
            **metadata,
        },
    )
