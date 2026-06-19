"""Optional Supabase REST cache for geocode results (requires SUPABASE_SERVICE_ROLE)."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def geocode_query_key(query: str) -> str:
    """Match client-side key in LocationSearchInput (lowercase trim, hash if >64)."""
    normalized = query.strip().lower()
    if len(normalized) <= 64:
        return normalized
    return hashlib.sha256(normalized.encode()).hexdigest()[:64]


def _headers() -> dict[str, str] | None:
    if not settings.supabase_service_role:
        return None
    key = settings.supabase_service_role
    return {"apikey": key, "Authorization": f"Bearer {key}"}


async def set_geocode_cache(query: str, results: list[dict[str, Any]]) -> None:
    """Upsert geocode results when service role is configured."""
    if not settings.supabase_url or not settings.supabase_service_role:
        return

    headers = _headers()
    if headers is None:
        return

    payload = [
        {
            "query_key": geocode_query_key(query),
            "query_text": query.strip(),
            "results": [
                {
                    "lat": float(item["lat"]),
                    "lng": float(item["lon"]),
                    "display_name": item["display_name"],
                }
                for item in results
            ],
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(hours=settings.cache_ttl_hours)
            ).isoformat(),
        }
    ]

    url = f"{settings.supabase_url.rstrip('/')}/rest/v1/geocode_cache"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                headers={
                    **headers,
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates",
                },
                json=payload,
            )
            response.raise_for_status()
    except Exception as exc:
        logger.debug("Supabase geocode cache write failed: %s", exc)
