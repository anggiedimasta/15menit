-- 15menit cache tables (Supabase / PostGIS)
-- Run via Supabase SQL editor or: supabase db push

CREATE EXTENSION IF NOT EXISTS postgis;

-- Geocode search results (Nominatim proxy cache)
CREATE TABLE IF NOT EXISTS geocode_cache (
    query_key VARCHAR(64) PRIMARY KEY,
    query_text TEXT NOT NULL,
    results JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_geocode_cache_expires ON geocode_cache (expires_at);

-- Isochrone polygons (Valhalla walk/car); API TieredCache also uses this via DATABASE_URL
CREATE TABLE IF NOT EXISTS isochrone_cache (
    cache_key VARCHAR(64) PRIMARY KEY,
    prefix VARCHAR(32) NOT NULL,
    geometry JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_isochrone_cache_expires ON isochrone_cache (expires_at);

-- RLS: anon read-only for geocode cache (optional client-side prefetch)
ALTER TABLE geocode_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY geocode_cache_anon_read ON geocode_cache
    FOR SELECT
    TO anon
    USING (expires_at > NOW());

-- Service role bypasses RLS for API writes (SUPABASE_SERVICE_ROLE)
