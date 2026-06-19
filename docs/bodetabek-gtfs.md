# Bodetabek GTFS merge

Extend Jakarta merged feed with Bogor / Bodetabek bus GTFS for r5py coverage beyond DKI.

## Bogor feed download

Official Pemkot GTFS is not always published at a stable URL. Practical sources:

| Source | URL | Notes |
|--------|-----|-------|
| Busmaps (Jakarta region) | https://busmaps.com/en/jakarta | Browse Bogor operators; export GTFS when offered |
| TransitFeeds archive | https://transitfeeds.com | Search "Bogor" / "DAMRI" / operator name |
| Pemkot Bogor open data | Portal varies by year | Check `bogorkota.go.id` / Satu Data portal |

### Steps

1. Download a valid GTFS zip for Bogor city buses (or Bodetabek operator you need).
2. Validate locally: zip must contain at least `stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`.
3. Save as `data/gtfs/bogor.zip` (gitignored; not committed).

```powershell
# After jakarta-merged.zip exists
python scripts/merge_bodetabek.py
```

Output: `data/gtfs/jakarta-bodetabek-merged.zip`

When `bogor.zip` is missing, the script copies Jakarta-only merged feed and logs `Skip missing Bogor feed`.

## Rebuild r5 network

After merge:

```powershell
pip install -e ".[transit]"   # from apps/api
# Requires data/osm/java-latest.osm.pbf + merged zip
$env:TRANSIT_MODE = "r5"
```

## Coverage bbox

Bodetabek bbox guard lives in API config — routes outside Jakarta core still need OSM extract + merged GTFS on disk.

## Gaps

- No automated Bogor download script (manual export until stable official URL).
- Bogor Central → Depok end-to-end pytest not yet wired (needs feed + r5 network in CI).
