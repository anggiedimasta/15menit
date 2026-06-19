# 15menit — Backlog

**Last updated:** Juni 2026  
**Ordering:** dependency → highest impact → lowest effort  
**Item format:** Flow · Data · Behavior · Tests  
**Status values:** Done · Partial · Blocked · Backlog  
**Summary:** 12 Done / 12 Partial

---

## Phase 0 — Foundation (P0)

> Blocker untuk semua phase. Impact: enable everything. Effort: medium.

### P0-01 Monorepo scaffold

**Priority:** P0 · **Effort:** S · **Impact:** Critical · **Deps:** none

**Flow:**
1. Init git repo → folder `apps/web` (TanStack Start) + `apps/api` (FastAPI) + `packages/shared`
2. Root `package.json` workspace (Bun) + `apps/api/pyproject.toml`
3. README dengan dev commands

**Data:**
- Input: none
- Output: runnable `bun run dev` (web) + `uvicorn` (api) hello world

**Behavior:**
- Web di `:3000`, API di `:8000`
- Health check `GET /health` → `{ "status": "ok" }`

**Tests:**
- `pytest`: health endpoint 200
- `vitest`: TanStack Start loads root page

**Status:** Done

---

### P0-02 Biome + Husky pre-commit

**Priority:** P0 · **Effort:** S · **Impact:** Medium · **Deps:** P0-01

**Flow:**
1. Install `@biomejs/biome` di root
2. `biome.json` — lint + format untuk TS/JSON
3. Husky pre-commit hook → `bun run lint:staged`

**Data:**
- Input: source files
- Output: zero biome errors on `biome check`

**Behavior:**
- `bun run lint` → biome check
- `bun run format` → biome format --write

**Tests:**
- CI fails on intentional lint violation (Biome step in `.github/workflows/ci.yml`)

**Status:** Done

---

### P0-03 Test infrastructure

**Priority:** P0 · **Effort:** S · **Impact:** High · **Deps:** P0-01

**Flow:**
1. Vitest + `@testing-library/react` di web
2. pytest + httpx di api
3. GitHub Actions: lint + test on push

**Data:**
- Input: test configs
- Output: green CI on push/PR

**Behavior:**
- `bun run test` (web) + `bun run test:api` (api) run in CI

**Tests:**
- Meta: sample tests pass in both apps

**Status:** Done

---

### P0-04 Docker compose (PostGIS + Valhalla placeholder)

**Priority:** P0 · **Effort:** M · **Impact:** High · **Deps:** P0-01

**Flow:**
1. `docker-compose.yml`: postgres/postgis, valhalla under `--profile routing`
2. `.env.example` with DB URL + routing mode vars
3. Alembic init for migrations *(planned)*

**Data:**
- Input: none
- Output: PostGIS ready on `:5432`; Valhalla on `:8002` when profile enabled

**Behavior:**
- `docker compose up -d db` → PostGIS accepts connections
- `docker compose --profile routing up -d valhalla` → routing service
- `alembic upgrade head` creates `isochrone_cache` (JSONB geometry + PostGIS extension)
- `TieredCache`: in-memory L1 + Postgres L2 when `DATABASE_URL` set; silent fallback if DB unavailable
- **Gap:** stops not in PostGIS; CI does not run DB integration tests

**Tests:**
- pytest: memory + tiered cache unit tests; PostGIS `ST_Point` + postgres cache round-trip — skipped unless `DATABASE_URL` set (`test_db_cache.py`)

**Status:** Partial — Alembic migration stub + tiered isochrone cache wired; stops table + CI DB job pending

---

### P0-05 Versioning + Husky pre-push

**Priority:** P0 · **Effort:** S · **Impact:** Medium · **Deps:** P0-02

**Flow:**
1. SemVer in root `package.json`
2. `scripts/release-sync.mjs` — changelog sync from conventional commits
3. Husky pre-push → `release-sync.mjs --if-needed` (patch bump)

**Data:**
- Input: git log since last release tag
- Output: updated `docs/changelog.md` + version bump commit

**Behavior:**
- Pre-push may require second push after auto changelog commit
- `bun run release:cut` for manual release

**Tests:**
- Manual: pre-push hook runs without error on clean tree

**Status:** Done

---

## Phase 1 — Jakarta Walking Isochrone (P0)

> Highest impact, lowest effort hero feature. Proves map + routing pipeline.

### P1-01 OSM extract pipeline (Java)

**Priority:** P0 · **Effort:** M · **Impact:** Critical · **Deps:** P0-04

**Flow:**
1. Download `java-latest.osm.pbf` from Geofabrik
2. Script `scripts/download-osm.sh` + `scripts/download-osm.ps1` + checksum verify
3. Store in `data/osm/` (gitignored)

**Data:**
- Input: Geofabrik URL
- Output: `data/osm/java-latest.osm.pbf` (~500MB)

**Behavior:**
- Re-run safe (skip if checksum match)
- Log file size + download date

**Tests:**
- pytest: scripts exist + mock file size > 100MB in CI (`test_osm_download.py`)

**Status:** Done

---

### P1-02 Valhalla walk isochrone service

**Priority:** P0 · **Effort:** L · **Impact:** Critical · **Deps:** P1-01, P0-04

**Flow:**
1. Build/import Valhalla graph from Java OSM (docker profile)
2. FastAPI: `POST /isochrone/walk`
3. Params: `{ lat, lng, minutes }`

**Data:**
- Input: `{ lat: -6.2, lng: 106.8, minutes: 15 }`
- Output: GeoJSON Polygon
- Source: OSM via Valhalla (or mock circles when `ROUTING_MODE=mock`)

**Behavior:**
- Return 400 if lat/lng outside Java bbox
- Cache in-memory by `(lat,lng,minutes,mode)` hash → TTL 24h
- Valhalla client in `app/services/routing.py`; mock fallback on error
- **Gap:** cache not in PostGIS as PRD spec; production Valhalla build not default

**Tests:**
- pytest: Monas polygon non-empty; 400 for (0,0); cache hit (`test_isochrone.py`)
- pytest: Valhalla client with mocked HTTP + `ROUTING_MODE=valhalla` path (`test_valhalla.py`)

**Status:** Partial — API + mock (street-grid irregular polygon, not circle) + Valhalla client + integration tests; prod graph build optional

---

### P1-03 TanStack Start map shell + floating glass UI

**Priority:** P0 · **Effort:** M · **Impact:** High · **Deps:** P0-01, P0-02

**Flow:**
1. MapLibre GL full-screen map (no sidebar/Sheet)
2. Glass panels float on top: top search, bottom mode chips, results card
3. Click map → drop pin → call API
4. Render GeoJSON polygon layer (Valhalla when `ROUTING_MODE=valhalla`)

**Data:**
- Input: user click `{ lat, lng }`
- Output: polygon overlay on map
- Source: `POST /isochrone/walk` / `POST /isochrone/car`

**Behavior:**
- Glassmorphism: `backdrop-blur-xl`, `bg-white/10`, border `white/20`, `rounded-2xl`
- Swiss typography: Inter/system-ui, tight tracking, minimal copy
- Icons > text: Phosphor icon buttons + tooltips + `aria-label`
- Mobile-first: bottom floating mode bar (Commute | Isochrone), thumb zone
- Slider: 10/15/30/45/60 min (isochrone glass panel)
- Dark/light map toggle (icon, glass)
- API health banner when backend unreachable
- Supabase geocode cache optional (`VITE_SUPABASE_*`); see `docs/setup-env.md`

**Tests:**
- vitest: map shell; compare disabled; style toggle; banners (`index.test.tsx`)
- e2e: floating UI mobile + desktop; no Sheet (`smoke.spec.ts`)

**Status:** Done — floating glass UI; sidebar/Sheet removed; `docs/setup-env.md` + `supabase/migrations/001_cache.sql`

---

### P1-04 Geocoding (Nominatim)

**Priority:** P1 · **Effort:** S · **Impact:** Medium · **Deps:** P1-03

**Flow:**
1. Search bar → Nominatim geocode (via FastAPI proxy, rate-limited)
2. Select result → fly to location + pin

**Data:**
- Input: `"Monas, Jakarta"`
- Output: `{ lat, lng, display_name }`
- Source: OSM Nominatim (self-host later)

**Behavior:**
- Debounce 300ms
- Bias results to Indonesia (`countrycodes=id`)
- Proxy prevents CORS + hides Nominatim from client
- Commute: **Dari** + **Ke** search fields (Google Maps pattern) set pins A/B
- Isochrone: **Titik asal** search field
- Vite dev proxy `/api` → `:8000` when `VITE_API_URL` unset

**Tests:**
- pytest: geocode "Monas" returns Jakarta coords (`test_geocode.py`)
- vitest: debounce doesn't fire before 300ms
- e2e: Monas search in Dari field (`smoke.spec.ts`)

**Status:** Done — dual From/To commute search + isochrone origin search + dev API proxy

---

## Phase 2 — Jakarta Transit + A→B Optimal Mode (P0)

> Core differentiator vs Moovit/Google. Highest product impact.

### P2-01 TransJakarta GTFS ingest

**Priority:** P0 · **Effort:** M · **Impact:** Critical · **Deps:** P0-04

**Flow:**
1. Download GTFS zip from official URL (`scripts/download_gtfs.py`)
2. Parse with `gtfs-kit` via `ingest_gtfs_from_zip`
3. Load stops/routes into PostGIS *(planned)*
4. Cron/script: weekly re-fetch

**Data:**
- Input: https://gtfs.transjakarta.co.id/files/file_gtfs.zip
- Output: parse stats; tables `stops`, `routes`, … *(PostGIS not wired)*
- Source: PT Transportasi Jakarta

**Behavior:**
- Log route count + stop count; warn if <200 routes
- **Gap:** stops served from JSON fixture + haversine `nearby_stops()`, not PostGIS

**Tests:**
- pytest: ingest produces >200 routes, >7000 stops (mock when gtfs-kit absent)

**Status:** Partial — download + parse scripts exist; PostGIS load not wired

---

### P2-02 KRL + MRT GTFS conversion

**Priority:** P0 · **Effort:** L · **Impact:** Critical · **Deps:** P2-01

**Flow:**
1. Fetch Comuline API → KRL stops + schedules *(attempt + static fallback)*
2. Fetch GIS DPMPTSP ArcGIS → MRT stop coords *(with static fallback)*
3. Convert to GTFS format → merge with TransJakarta feed
4. Output: `data/gtfs/jakarta-merged.zip`

**Data:**
- Input: Comuline API, ArcGIS FeatureServer, static `mrt_stops.json`
- Output: unified GTFS zip (TJ-only when single input)
- Source: community + Pemprov DKI

**Behavior:**
- `scripts/fetch_krl_stops.py` hits Comuline `/v1/station`, merges Jakarta KRL list with static coords (Comuline has no lat/lng); logs failure → full static fallback
- `scripts/fetch_mrt_stops.py` queries DPMPTSP ArcGIS (`fungsi LIKE '%STASIUN MRT%'`), falls back to `data/gtfs/static/mrt_stops.json`
- `scripts/fetch_lrt_stops.py` queries DPMPTSP ArcGIS (`fungsi LIKE '%STASIUN LRT%'`), supplements Jakarta LRT from static when GIS is Jabodebek-only; falls back to full static
- `scripts/build_krl_gtfs.py` + `scripts/build_mrt_gtfs.py` + `scripts/build_lrt_gtfs.py` build minimal GTFS zips (LRT-JKT + LRT-JBD routes)
- `scripts/merge_gtfs.py` CSV-merge + 50m stop dedup when multiple feeds; includes `lrt_minimal.zip` in default inputs
- **Gap:** Comuline coords still from static overlay; live KRL/MRT/LRT schedules synthetic (stop_times MVP only); TJ official zip optional locally

**Tests:**
- pytest: KRL + MRT + LRT pipeline + merge when TJ zip present (`test_gtfs.py`)

**Status:** Partial — ArcGIS MRT/LRT + Comuline station list wired; static coord overlay + synthetic schedules; prod TJ zip + real timetables pending

---

### P2-03 r5py transit isochrone

**Priority:** P0 · **Effort:** L · **Impact:** Critical · **Deps:** P1-01, P2-02

**Flow:**
1. Build r5py `TransportNetwork(osm_pbf, gtfs=[merged])`
2. FastAPI: `POST /isochrone/transit`
3. Same interface as walk isochrone

**Data:**
- Input: `{ lat, lng, minutes: 30 }`
- Output: GeoJSON Polygon (reachable by walk+transit)
- Source: OSM + merged GTFS via r5py (mock expanded walk by default)

**Behavior:**
- Default departure: next weekday 07:30 WIB
- Return metadata: `{ modes_used, departure_time }`
- Mock: expanded walk polygon (1.35× radius); area ≥ walk sanity test
- Fallback expanded walk when r5 build fails or `TRANSIT_MODE=mock`

**Tests:**
- pytest: transit vs walk area comparison (`test_isochrone.py`)

**Status:** Partial — endpoint + mock/r5 paths + area test; prod r5 network optional

---

### P2-04 A→B mode comparison engine

**Priority:** P0 · **Effort:** L · **Impact:** Critical · **Deps:** P1-02, P2-03

**Flow:**
1. User set pin A + pin B
2. API `POST /commute/compare` runs walk / transit / car / motor
3. Rank by duration → mark `is_fastest`

**Data:**
- Input: `{ origin: {lat,lng}, destination: {lat,lng}, departure?: ISO8601 }`
- Output: `fastest_mode`, `results[]` with duration, cost, legs

**Behavior:**
- Badge "Paling cepat" on fastest
- If delta <5 min between top 2 → `note: "Selisih tipis"`
- Transit legs from `plan_transit_route()` — GTFS `stop_times` + `route_long_name` when merged feed present; `_line_name_for_stop()` resolves TJ/KRL/MRT/LRT names from merged routes; agency from GTFS stop_id prefix; haversine heuristic fallback; r5 duration when `TRANSIT_MODE=r5`
- Returns `route_polyline` for map overlay; transit leg includes `line_name` (GTFS route name or agency default incl. LRT Jakarta / LRT Jabodebek)

**Tests:**
- pytest: fastest_mode + 5 fixture pairs; transit legs + polyline + line_name + GTFS stop_times (`test_commute.py`, `test_transit_gtfs.py`)

**Status:** Partial — GTFS stop_times + route_long_name legs + LRT agency detection; r5 leg-by-leg detail still pending

---

### P2-05 A→B UI (two-pin flow)

**Priority:** P0 · **Effort:** M · **Impact:** High · **Deps:** P2-04, P1-03

**Flow:**
1. Toggle "Isochrone" / "Commute" mode
2. Commute mode: pin A (hijau) + pin B (merah)
3. "Bandingkan moda" button → comparison panel

**Data:**
- Input: two pins from map
- Output: comparison cards
- Source: `POST /commute/compare`

**Behavior:**
- Swap A↔B button
- Remember last A/B in sessionStorage
- Share URL: `?a=lat,lng&b=lat,lng&mode=commute` read/write on load
- Expandable transit card → route polyline on map
- `data-testid` on map, compare button, comparison cards (e2e selectors)
- Google Maps-style **Dari** / **Ke** search with pin icons + swap
- Full-width **Bandingkan moda** CTA; comparison cards with mode icons + fastest highlight
- Map markers labeled Dari / Ke / Titik asal (pulsing origin on isochrone)

**Tests:**
- vitest: swap exchanges pins; compare disabled; transit expand emits polyline; share URL parse/build; comparison card testids (`index.test.tsx`, `shareUrl.test.ts`)
- e2e: commute route inputs, Monas geocode, origin marker on isochrone click

**Status:** Done — floating glass commute UX; Dari/Ke top card; icon compare; labeled markers (Dari/Ke/Asal)

**Gap:** sessionStorage last A/B not implemented

---

### P2-06 Transit fare estimation

**Priority:** P1 · **Effort:** M · **Impact:** Medium · **Deps:** P2-04

**Flow:**
1. TJ flat fare Rp 3.500
2. KRL fare from station-pair matrix
3. MRT fare from segment count

**Data:**
- Input: transit legs with agency + stops
- Output: `cost_idr` per mode
- Source: `data/fares/jakarta.json`

**Behavior:**
- Fare breakdown in API response
- `null` cost if fare unknown (don't guess)

**Tests:**
- pytest: TJ-only = 3500; KRL Manggarai→Sudirman = 5000

**Status:** Done

---

## Phase 3 — Car & Motor routing (P1)

> After transit works. Motor derived from Valhalla motorcycle profile.

### P3-01 Valhalla car isochrone + route

**Priority:** P1 · **Effort:** M · **Impact:** High · **Deps:** P1-02

**Flow:**
1. Add `auto` costing to Valhalla build
2. `POST /isochrone/car`, extend `/commute/compare` with car

**Data:**
- Input: same as walk
- Output: GeoJSON polygon / route
- Source: OSM (no live traffic); mock when `ROUTING_MODE=mock`

**Behavior:**
- Disclaimer: "Estimasi tanpa traffic real-time"
- Car isochrone typically larger than walk

**Tests:**
- pytest: car isochrone area > walk (`test_car.py`)

**Status:** Partial — API + car isochrone UI (walk/mobil toggle); prod Valhalla optional

---

### P3-02 Motor profile (derived)

**Priority:** P1 · **Effort:** S · **Impact:** Medium · **Deps:** P3-01

**Flow:**
1. Add `motorcycle` costing to Valhalla
2. Expose in compare endpoint as separate mode

**Data:**
- Input: same as car
- Output: duration typically ≤ car duration
- Source: Valhalla motorcycle profile (or mock speeds)

**Behavior:**
- Show motor in comparison, not separate isochrone slider
- Label: "Motor (estimasi)"

**Tests:**
- pytest: motor duration <= car duration same A→B

**Status:** Partial — compare shows car + motor cards (pytest + vitest); motor not separate isochrone per spec; prod Valhalla optional

---

## Phase 4 — Multi-origin & Coverage (P2)

### P4-01 Nearby stops query

**Priority:** P2 · **Effort:** M · **Impact:** Medium · **Deps:** P2-01

**Flow:**
1. Given point, `ST_DWithin` stops within 500m–1km *(spec)*
2. Return stop list with walking distance

**Data:**
- Input: `{ lat, lng, radius_m: 800 }`
- Output: `[{ stop_id, name, distance_m, modes }]`

**Behavior:**
- Default radius 800m; sort by distance asc
- `load_stops()` prefers `data/gtfs/jakarta-merged.zip` (or `GTFS_MERGED_PATH`); falls back to fixture JSON
- **Gap:** haversine over in-memory list, not PostGIS `ST_DWithin`

**Tests:**
- pytest: Monas point returns nearby stops (`test_stops.py`, `test_gtfs_stops.py`)

**Status:** Partial — merged GTFS zip load wired; PostGIS spatial query pending

---

### P4-02 Multi-origin union isochrone

**Priority:** P2 · **Effort:** L · **Impact:** Medium · **Deps:** P4-01, P2-03

**Flow:**
1. Get nearby stops → isochrone from each stop origin
2. Union polygons (shapely `unary_union`)
3. Optional heatmap layer *(deferred)*

**Data:**
- Input: home point + `max_origins`
- Output: union GeoJSON

**Behavior:**
- Cap max origins at 20 (configurable)
- **Gap:** no web UI; call `POST /stops/multi-origin-isochrone` directly
- **Gap:** heatmap grid layer not in UI

**Tests:**
- pytest: union area >= any single isochrone (`test_stops.py`)

**Status:** Partial — API union works; web UI + heatmap deferred

---

### P4-03 Kecamatan coverage score

**Priority:** P2 · **Effort:** L · **Impact:** Medium · **Deps:** P2-03

**Flow:**
1. Load kecamatan boundaries (OSM admin or BPS shapefile) *(not loaded)*
2. Sample grid points → % reachable in 15min transit

**Data:**
- Input: `kecamatan_id`
- Output: `{ coverage_pct, sample_count }`

**Behavior:**
- Precompute nightly for T1 *(stub: deterministic mock from id hash)*
- Color choropleth on map *(not implemented)*

**Tests:**
- pytest: coverage_pct between 0–100

**Status:** Partial — `GET /coverage/kecamatan/{id}` stub only; boundaries + choropleth map layer + nightly job pending

---

## Phase 5 — Bodetabek expansion (P1)

### P5-01 Bogor + Bodetabek GTFS merge

**Priority:** P1 · **Effort:** L · **Impact:** High · **Deps:** P2-02

**Flow:**
1. Ingest Bogor GTFS (Pemkot) when available
2. Extend OSM extract or use full Java
3. Rebuild r5py network

**Data:**
- Input: busmaps Bogor feed + existing Jakarta merged
- Output: `jakarta-bodetabek-merged.zip`

**Behavior:**
- `scripts/merge_bodetabek.py` skips missing Bogor zip gracefully; see `docs/bodetabek-gtfs.md` for manual download → `data/gtfs/bogor.zip`
- Bbox guard expands to Bodetabek in config

**Tests:**
- pytest: merge skips missing Bogor + produces `jakarta-bodetabek-merged.zip` (`test_gtfs.py::test_merge_bodetabek_skips_missing_bogor`); Bogor Central → Depok transit — **not implemented**

**Status:** Partial — merge script + `docs/bodetabek-gtfs.md` + skip test; Bogor feed bundle + r5 rebuild optional

---

## Phase 6 — Major cities (P2)

### P6-01 City template pipeline

**Priority:** P2 · **Effort:** L · **Impact:** High · **Deps:** P5-01

**Flow:**
1. `scripts/add-city.ts` — config-driven: `{ city, gtfs_urls, osm_extract, bbox }`
2. Document per-city data gaps

**Data:**
- Input: city config YAML (`cities/bandung.yaml`)
- Output: `data/cities/{city}/manifest.json`

**Behavior:**
- Cities: Bandung, Surabaya, Yogyakarta, Semarang (ordered)
- Skip city if no GTFS → walk+car only + warning banner

**Tests:**
- pytest: template produces manifest for Bandung (`test_city_template.py`)

**Status:** Done — `bun scripts/add-city.ts cities/bandung.yaml` verified; pytest `test_city_template.py`

---

## Phase 7 — Minor cities + polish (P3)

### P7-01 Walk+car fallback mode

**Priority:** P3 · **Effort:** M · **Impact:** Low · **Deps:** P3-01, P6-01

**Flow:**
1. Detect no GTFS for bbox → disable transit features
2. Show banner: "Data transit belum tersedia di kota ini"

**Behavior:**
- `GET /meta/city` → `transit_available: false` when `TRANSIT_MODE=disabled`
- Graceful degradation, not error page

**Tests:**
- vitest: banner shows when API returns `transit_available: false`

**Status:** Done

---

### P7-02 PWA + performance pass

**Priority:** P3 · **Effort:** M · **Impact:** Medium · **Deps:** all core

**Flow:**
1. Service worker cache static assets (`/sw.js`, manifest)
2. Lighthouse mobile score >80 *(not verified in CI)*
3. API response compression (gzip)

**Tests:**
- Lighthouse CI warn thresholds (≥0.8) in `.github/workflows/ci.yml` + `lighthouserc.json`

**Status:** Partial — PWA shell + gzip + Lighthouse CI (warn-only); mobile preset + error thresholds pending

---

## Notes & blockers

| Item | Note |
|------|------|
| Valhalla production | Use `docker compose --profile routing`; first build is slow/OOM-prone |
| r5py production | Requires `pip install -e ".[transit]"` + OSM + merged GTFS |
| KRL/MRT/LRT merge | Comuline `/v1/station` + static coords; ArcGIS MRT/LRT live; LRT Jakarta static supplement; synthetic stop_times in minimal feeds |
| PostGIS / Supabase cache | Docker DB + Alembic `isochrone_cache`; Supabase migration `001_cache.sql` adds `geocode_cache`; API geocode DB write still pending |
| P4-02 multi-origin UI | API `POST /stops/multi-origin-isochrone` only; no web panel |
| P4-03 choropleth UI | API stub only; map layer deferred |
| Lighthouse CI | Warn thresholds in CI; tighten to error + mobile preset when stable |

---

## Dependency Graph (summary)

```
P0 (foundation)
 └─► P1 (walk isochrone) ──► P1-04 geocode
      └─► P2 (transit + A→B) ──► P2-05 UI
           ├─► P3 (car/motor)
           ├─► P4 (multi-origin, coverage)
           └─► P5 (Bodetabek)
                └─► P6 (major cities)
                     └─► P7 (fallback + polish)
```

## Recommended Sprint Order

| Sprint | Items | Goal |
|--------|-------|------|
| S1 | P0-01 → P0-05 | Repo + CI + DB + release hooks |
| S2 | P1-01 → P1-03 | **Demo: walking isochrone on map** |
| S3 | P2-01 → P2-03 | Transit isochrone works |
| S4 | P2-04 → P2-05 | **Demo: A→B optimal mode** ← killer feature |
| S5 | P2-06, P3-01 → P3-02 | Fare + car/motor |
| S6 | P4-*, P5-01 | Coverage + Bodetabek |
| S7 | P6-*, P7-* | Multi-city + polish |
