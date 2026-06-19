/**
 * Optional Supabase client for client-side cache reads (geocode_cache).
 * Accepts publishable key (`sb_publishable_*`) or legacy JWT anon key.
 * Server writes use SUPABASE_SERVICE_ROLE in the API when configured.
 * API reads the same project URL from VITE_SUPABASE_URL (see config.py fallback).
 */

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export type GeocodeCacheRow = {
  query_key: string;
  results: Array<{ lat: number; lng: number; display_name: string }>;
};

/**
 * Lazy REST fetch — avoids bundling @supabase/supabase-js until needed.
 */
export async function fetchGeocodeCache(
  queryKey: string,
): Promise<GeocodeCacheRow["results"] | null> {
  if (!isSupabaseConfigured || !supabaseAnonKey) return null;

  const key = supabaseAnonKey;

  const url = new URL(`${supabaseUrl}/rest/v1/geocode_cache`);
  url.searchParams.set("query_key", `eq.${queryKey}`);
  url.searchParams.set("select", "results,expires_at");
  url.searchParams.set("expires_at", `gt.${new Date().toISOString()}`);

  try {
    const response = await fetch(url.toString(), {
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
      },
    });
    if (!response.ok) return null;
    const rows = (await response.json()) as Array<{
      results: GeocodeCacheRow["results"];
    }>;
    return rows[0]?.results ?? null;
  } catch {
    return null;
  }
}
