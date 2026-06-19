from fastapi import APIRouter, HTTPException

from app.core.bbox import in_java_bbox
from app.models.schemas import CommuteCompareRequest, CommuteCompareResponse
from app.services.commute import compare_commute

router = APIRouter(prefix="/commute", tags=["commute"])


@router.post("/compare", response_model=CommuteCompareResponse)
async def commute_compare(body: CommuteCompareRequest) -> CommuteCompareResponse:
    if not in_java_bbox(body.origin.lat, body.origin.lng):
        raise HTTPException(status_code=400, detail="Origin outside service area")
    if not in_java_bbox(body.destination.lat, body.destination.lng):
        raise HTTPException(status_code=400, detail="Destination outside service area")
    return await compare_commute(body)
