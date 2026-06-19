from typing import Any, Literal

from pydantic import BaseModel, Field


class LatLng(BaseModel):
    lat: float
    lng: float


class IsochroneRequest(BaseModel):
    lat: float
    lng: float
    minutes: int = Field(default=15, ge=5, le=120)


class IsochroneResponse(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any]


class GeocodeResult(BaseModel):
    lat: float
    lng: float
    display_name: str


class TransitLeg(BaseModel):
    mode: str
    route_id: str | None = None
    line_name: str | None = None
    board_stop: str | None = None
    alight_stop: str | None = None
    duration_min: int | None = None


class CommuteModeResult(BaseModel):
    mode: Literal["walking", "transit", "car", "motorcycle"]
    duration_min: int
    distance_m: int | None = None
    transfers: int | None = None
    legs: list[TransitLeg] = Field(default_factory=list)
    route_polyline: list[list[float]] | None = None
    cost_idr: int | None = None
    is_fastest: bool = False
    fare_breakdown: list[dict[str, Any]] | None = None


class CommuteCompareRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    departure: str | None = None


class CommuteCompareResponse(BaseModel):
    fastest_mode: str
    note: str | None = None
    transit_available: bool = True
    results: list[CommuteModeResult]


class NearbyStopsRequest(BaseModel):
    lat: float
    lng: float
    radius_m: int = Field(default=800, ge=100, le=2000)


class StopInfo(BaseModel):
    stop_id: str
    name: str
    distance_m: int
    modes: list[str]


class MultiOriginRequest(BaseModel):
    lat: float
    lng: float
    minutes: int = 15
    max_origins: int = Field(default=20, ge=1, le=20)


class CoverageRequest(BaseModel):
    kecamatan_id: str


class CoverageResponse(BaseModel):
    kecamatan_id: str
    coverage_pct: float
    sample_count: int
