import os
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.env_loader import load_root_env

load_root_env()

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _merged_gtfs_path() -> Path:
    env_path = os.getenv("GTFS_MERGED_PATH")
    if env_path:
        candidate = Path(env_path)
        if not candidate.is_absolute():
            candidate = _REPO_ROOT / candidate
        return candidate
    return _REPO_ROOT / "data" / "gtfs" / "jakarta-merged.zip"


def _probe_valhalla(url: str) -> bool:
    try:
        response = httpx.get(f"{url.rstrip('/')}/status", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def _resolve_routing_mode(valhalla_url: str, valhalla_reachable: bool) -> str:
    explicit = os.getenv("ROUTING_MODE", "auto").strip().lower()
    if explicit == "mock":
        return "mock"
    if explicit == "valhalla":
        return "valhalla"
    if valhalla_reachable:
        return "valhalla"
    return "mock"


def _resolve_transit_mode(gtfs_path: Path) -> str:
    explicit = os.getenv("TRANSIT_MODE", "mock").strip().lower()
    if explicit in ("gtfs", "r5", "disabled", "mock"):
        return explicit
    if explicit == "auto" and gtfs_path.exists():
        return "gtfs"
    return "mock"


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    valhalla_url: str
    nominatim_url: str
    routing_mode: str
    transit_mode: str
    gtfs_merged_path: Path
    valhalla_reachable: bool
    gtfs_merged_available: bool
    java_bbox: tuple[float, float, float, float]
    bodetabek_bbox: tuple[float, float, float, float]
    cache_ttl_hours: int
    geocode_rate_limit_per_sec: float
    supabase_url: str | None
    supabase_service_role: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        valhalla_url = os.getenv("VALHALLA_URL", "http://localhost:8002")
        gtfs_path = _merged_gtfs_path()
        valhalla_reachable = _probe_valhalla(valhalla_url)
        return cls(
            database_url=os.getenv("DATABASE_URL"),
            valhalla_url=valhalla_url,
            nominatim_url=os.getenv(
                "NOMINATIM_URL", "https://nominatim.openstreetmap.org"
            ),
            routing_mode=_resolve_routing_mode(valhalla_url, valhalla_reachable),
            transit_mode=_resolve_transit_mode(gtfs_path),
            gtfs_merged_path=gtfs_path,
            valhalla_reachable=valhalla_reachable,
            gtfs_merged_available=gtfs_path.exists(),
            java_bbox=(-8.85, 105.0, -5.5, 114.5),
            bodetabek_bbox=(-6.75, 106.3, -6.0, 107.2),
            cache_ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "24")),
            geocode_rate_limit_per_sec=float(
                os.getenv("GEOCODE_RATE_LIMIT_PER_SEC", "1")
            ),
            supabase_url=os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL"),
            supabase_service_role=os.getenv("SUPABASE_SERVICE_ROLE"),
        )


settings = Settings.from_env()
