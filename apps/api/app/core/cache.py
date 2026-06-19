import hashlib
import json
import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class MemoryCache:
    def __init__(self, ttl_seconds: int = 86400) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl_seconds

    def _key(self, prefix: str, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True)
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{prefix}:{digest}"

    def get(self, prefix: str, payload: dict[str, Any]) -> Any | None:
        key = self._key(prefix, payload)
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, prefix: str, payload: dict[str, Any], value: Any) -> None:
        key = self._key(prefix, payload)
        self._store[key] = (time.time() + self._ttl, value)


class PostgresCache:
    """Optional PostGIS-backed isochrone cache. Requires DATABASE_URL + alembic migration."""

    def __init__(self, database_url: str, ttl_seconds: int = 86400) -> None:
        self._database_url = database_url
        self._ttl = ttl_seconds

    def _key(self, prefix: str, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True)
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{prefix}:{digest}"

    def get(self, prefix: str, payload: dict[str, Any]) -> Any | None:
        try:
            import psycopg
        except ImportError:
            return None

        key = self._key(prefix, payload)
        try:
            with psycopg.connect(self._database_url, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT geometry
                        FROM isochrone_cache
                        WHERE cache_key = %s AND expires_at > NOW()
                        """,
                        (key,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        return None
                    return row[0]
        except Exception as exc:
            logger.debug("Postgres cache get failed: %s", exc)
            return None

    def set(self, prefix: str, payload: dict[str, Any], value: Any) -> None:
        try:
            import psycopg
            from psycopg.types.json import Jsonb
        except ImportError:
            return

        key = self._key(prefix, payload)
        try:
            with psycopg.connect(self._database_url, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO isochrone_cache (cache_key, prefix, geometry, expires_at)
                        VALUES (%s, %s, %s, NOW() + make_interval(secs => %s))
                        ON CONFLICT (cache_key) DO UPDATE
                        SET geometry = EXCLUDED.geometry,
                            expires_at = EXCLUDED.expires_at
                        """,
                        (key, prefix, Jsonb(value), self._ttl),
                    )
                conn.commit()
        except Exception as exc:
            logger.debug("Postgres cache set failed: %s", exc)


class TieredCache:
    """In-memory L1 with optional Postgres L2 when DATABASE_URL is set."""

    def __init__(self, ttl_seconds: int = 86400) -> None:
        self._memory = MemoryCache(ttl_seconds=ttl_seconds)
        self._postgres: PostgresCache | None = None
        if settings.database_url:
            self._postgres = PostgresCache(settings.database_url, ttl_seconds=ttl_seconds)

    def get(self, prefix: str, payload: dict[str, Any]) -> Any | None:
        cached = self._memory.get(prefix, payload)
        if cached is not None:
            return cached
        if self._postgres is None:
            return None
        cached = self._postgres.get(prefix, payload)
        if cached is not None:
            self._memory.set(prefix, payload, cached)
        return cached

    def set(self, prefix: str, payload: dict[str, Any], value: Any) -> None:
        self._memory.set(prefix, payload, value)
        if self._postgres is not None:
            self._postgres.set(prefix, payload, value)


isochrone_cache = TieredCache(ttl_seconds=settings.cache_ttl_hours * 3600)
