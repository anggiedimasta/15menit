from fastapi import APIRouter

from app.models.schemas import CoverageRequest, CoverageResponse
from app.services.commute import coverage_score

router = APIRouter(prefix="/coverage", tags=["coverage"])


@router.post("/kecamatan", response_model=CoverageResponse)
async def kecamatan_coverage(body: CoverageRequest) -> CoverageResponse:
    result = coverage_score(body.kecamatan_id)
    return CoverageResponse(**result)
