from fastapi import APIRouter, HTTPException, Query

from app.core.bbox import in_java_bbox
from app.core.cache import isochrone_cache
from app.models.schemas import GeocodeResult, IsochroneRequest, IsochroneResponse
from app.services.geocode import search_geocode
from app.services.supabase_cache import set_geocode_cache
from app.services.routing import get_isochrone

router = APIRouter(tags=["geocode"])


@router.get("/geocode/search")
async def geocode_search(q: str = Query(min_length=2)) -> list[GeocodeResult]:
    raw = await search_geocode(q)
    await set_geocode_cache(q, raw)
    return [
        GeocodeResult(
            lat=float(item["lat"]),
            lng=float(item["lon"]),
            display_name=item["display_name"],
        )
        for item in raw
    ]
