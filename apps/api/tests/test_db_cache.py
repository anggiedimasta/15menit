import os

import pytest

from app.core.cache import MemoryCache, TieredCache


def test_memory_cache_round_trip() -> None:
    cache = MemoryCache(ttl_seconds=60)
    payload = {"lat": -6.17, "lng": 106.82, "minutes": 15, "mode": "walk"}
    geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}

    assert cache.get("isochrone", payload) is None
    cache.set("isochrone", payload, geometry)
    assert cache.get("isochrone", payload) == geometry


def test_tiered_cache_without_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from app.config import Settings

    monkeypatch.setattr("app.core.cache.settings", Settings.from_env())
    cache = TieredCache(ttl_seconds=60)
    payload = {"lat": -6.17, "lng": 106.82, "minutes": 15, "mode": "walk"}
    geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}

    cache.set("isochrone", payload, geometry)
    assert cache.get("isochrone", payload) == geometry


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set — run docker compose up -d db && alembic upgrade head",
)
def test_postgis_st_point_query() -> None:
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            cur.execute(
                "SELECT ST_AsText(ST_SetSRID(ST_Point(%s, %s), 4326))",
                (106.8272, -6.1754),
            )
            row = cur.fetchone()
    assert row is not None
    assert "POINT" in row[0]


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set — requires migrated isochrone_cache table",
)
def test_isochrone_cache_postgres_round_trip() -> None:
    from app.core.cache import PostgresCache

    cache = PostgresCache(os.environ["DATABASE_URL"], ttl_seconds=3600)
    payload = {"lat": -6.17, "lng": 106.82, "minutes": 15, "mode": "walk"}
    geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}

    cache.set("isochrone", payload, geometry)
    assert cache.get("isochrone", payload) == geometry
