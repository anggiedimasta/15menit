import asyncio
import time
from typing import Any

import httpx

from app.config import settings

_last_request_at = 0.0
_rate_lock = asyncio.Lock()


async def _rate_limit() -> None:
    global _last_request_at
    async with _rate_lock:
        min_interval = 1.0 / settings.geocode_rate_limit_per_sec
        elapsed = time.time() - _last_request_at
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        _last_request_at = time.time()


async def search_geocode(query: str, mock: bool = False) -> list[dict[str, Any]]:
    if mock or settings.routing_mode == "mock":
        return _mock_results(query)

    await _rate_limit()
    params = {
        "q": query,
        "format": "json",
        "limit": 5,
        "countrycodes": "id",
    }
    headers = {"User-Agent": "15menit/0.1 (transit accessibility app)"}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"{settings.nominatim_url}/search",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


def _mock_results(query: str) -> list[dict[str, Any]]:
    q = query.lower()
    if "monas" in q:
        return [
            {
                "lat": "-6.1754",
                "lon": "106.8272",
                "display_name": "Monumen Nasional, Jakarta Pusat, Indonesia",
            }
        ]
    if "sudirman" in q:
        return [
            {
                "lat": "-6.2088",
                "lon": "106.8456",
                "display_name": "Sudirman, Jakarta, Indonesia",
            }
        ]
    return [
        {
            "lat": "-6.2000",
            "lon": "106.8167",
            "display_name": f"{query}, Jakarta, Indonesia",
        }
    ]
