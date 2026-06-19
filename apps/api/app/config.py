import os
from dataclasses import dataclass

from app.env_loader import load_root_env

load_root_env()


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    valhalla_url: str
    nominatim_url: str
    routing_mode: str
    transit_mode: str
    java_bbox: tuple[float, float, float, float]
    bodetabek_bbox: tuple[float, float, float, float]
    cache_ttl_hours: int
    geocode_rate_limit_per_sec: float
    supabase_url: str | None
    supabase_service_role: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL"),
            valhalla_url=os.getenv("VALHALLA_URL", "http://localhost:8002"),
            nominatim_url=os.getenv(
                "NOMINATIM_URL", "https://nominatim.openstreetmap.org"
            ),
            routing_mode=os.getenv("ROUTING_MODE", "mock"),
            transit_mode=os.getenv("TRANSIT_MODE", "mock"),
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
