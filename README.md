# 15menit

Indonesian transit accessibility app — commute mode comparison & isochrone maps.

## Docs

- [PRD](docs/prd.md)
- [Backlog](docs/backlog.md)
- [Changelog](docs/changelog.md)

## Prerequisites

- [Bun](https://bun.sh)
- Python 3.12+
- Docker (optional — PostGIS + Valhalla)

## Setup

```powershell
bun install
cd apps/api ; pip install -e ".[dev]"
cp .env.example .env
```

## Development

```powershell
# Web (TanStack Start) — http://localhost:3000
bun run dev

# API (FastAPI) — http://localhost:8000
bun run dev:api

# Stable API for E2E (no --reload; avoids Windows reloader exit)
bun run dev:api:stable
```

Default routing uses **mock mode** (no Valhalla/r5py required). Set in `.env`:

| Variable | Values | Purpose |
|----------|--------|---------|
| `ROUTING_MODE` | `mock` / `valhalla` | Street routing |
| `TRANSIT_MODE` | `mock` / `r5` / `disabled` | Transit isochrone + compare |
| `VALHALLA_URL` | `http://localhost:8002` | Valhalla service |

## Hero flow: A→B commute compare

1. Open http://localhost:3000 (Commute tab is default)
2. Click map for pin **A** (green), then pin **B** (red)
3. Click **Bandingkan moda** — cards rank walk / transit / car / motor
4. Fastest mode gets **Paling cepat** badge

## Isochrone demo

1. Switch to **Isochrone** tab
2. Search "Monas" or click map
3. Adjust slider (10–60 min) — walk polygon updates

## Data pipeline

```powershell
# OSM extract (~500MB, gitignored)
powershell -File scripts/download-osm.ps1

# TransJakarta GTFS
python scripts/download_gtfs.py
python scripts/fetch_krl_stops.py
python scripts/build_krl_gtfs.py
python scripts/fetch_mrt_stops.py
python scripts/build_mrt_gtfs.py
python scripts/fetch_lrt_stops.py
python scripts/build_lrt_gtfs.py
python scripts/merge_gtfs.py

# Bodetabek merge (download Bogor GTFS to data/gtfs/bogor.zip first)
python scripts/merge_bodetabek.py

# City template (Bandung etc.)
bun scripts/add-city.ts cities/bandung.yaml
```

### Valhalla (optional, heavy build)

```powershell
docker compose --profile routing up -d valhalla
# Set ROUTING_MODE=valhalla in .env
```

### r5py transit (optional)

Requires Java OSM PBF + merged GTFS in `data/`. Install: `pip install -e ".[transit]"`. Set `TRANSIT_MODE=r5`.

## Tests

```powershell
bun run test        # Vitest (web)
bun run test:api    # pytest (api)
bun run test:all    # both
bun run test:e2e    # Playwright smoke (6 scenarios)
```

Use `dev:api:stable` when running E2E locally. Playwright config already starts API without reload.

CI runs with `ROUTING_MODE=mock` — no external services.

## Database (optional)

```powershell
docker compose up -d db
```

PostGIS on `:5432`. Isochrone cache uses in-memory store by default.

## Monorepo layout

```
apps/web/       TanStack Start + shadcn + MapLibre
apps/api/       FastAPI — isochrone, commute, geocode, stops
packages/shared TS types
scripts/        OSM/GTFS download, city template
data/           gitignored extracts + committed fare tables
cities/         per-city YAML configs (P6)
```

## PWA

Service worker at `/sw.js` caches shell assets. Web manifest at `/manifest.webmanifest`.

## Lint & format

```powershell
bun run lint
bun run format
```

Pre-commit: Biome on staged files. Pre-push: changelog sync + patch bump.
