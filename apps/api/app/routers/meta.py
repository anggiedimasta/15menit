from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["meta"])


@router.get("/meta/city")
async def city_meta() -> dict:
    return {
        "city": "jakarta",
        "transit_available": settings.transit_mode != "disabled",
        "routing_mode": settings.routing_mode,
        "valhalla_reachable": settings.valhalla_reachable,
        "gtfs_merged_available": settings.gtfs_merged_available,
        "bbox": {
            "java": settings.java_bbox,
            "bodetabek": settings.bodetabek_bbox,
        },
    }
