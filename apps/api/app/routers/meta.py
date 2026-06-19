from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["meta"])


@router.get("/meta/city")
async def city_meta() -> dict:
    return {
        "city": "jakarta",
        "transit_available": settings.transit_mode != "disabled",
        "routing_mode": settings.routing_mode,
        "bbox": {
            "java": settings.java_bbox,
            "bodetabek": settings.bodetabek_bbox,
        },
    }
