# PRD: 15menit

**Product Name:** 15menit  
**Version:** 1.4 (MVP — versioning + git hooks)  
**Date:** Juni 2026  
**Vision:** Membantu warga Indonesia memahami aksesibilitas transportasi kota mereka secara akurat, serta mendukung keputusan commuting dan perencanaan kota.

**Prinsip MVP:** Works best first. Privacy & monetization ditunda.

---

## 0. MVP North Star

**Satu kalimat:** User pin rumah/kos (A) + kantor/sekolah (B) → app jawab **moda mana paling cepat**, berapa menit, transfer berapa, estimasi biaya.

**Hero feature:** Optimal Commute Mode (A → B) — bukan isochrone.  
**Secondary feature:** Isochrone (wow factor demo + housing exploration).  
**Milestone demo (Sprint 4):** Video 2 menit — pin Sudirman → SCBD → "Transit paling cepat, ~28 menit, 1× transfer TJ→MRT" + isochrone 15 menit walk dari Monas.

**Differentiator vs Moovit/Google Maps:** Navigation vs **decision tool** — isochrone visual + side-by-side mode comparison untuk pilih kos/kantor, bukan cuma A→B directions.

---

## 1. Problem Statement

- Macet kronis di kota-kota besar Indonesia.
- Coverage transportasi umum (TransJakarta, MRT, KRL, Bus, dll) tidak merata.
- Sulit bagi warga menilai lokasi rumah/kos/kantor berdasarkan akses transit yang realistis.
- Sulit membandingkan moda commuting (jalan kaki, transit, mobil) dari titik A ke titik B dalam satu layar.
- Pemerintah dan perencana kota kesulitan mendapatkan data coverage yang cepat dan visual.

---

## 2. Goal & Objectives

| Prioritas | Objective |
|-----------|-----------|
| P0 | Jawab **moda tercepat A→B** beserta rute transit, durasi, transfer, estimasi biaya |
| P0 | **Walking + transit** akurat untuk Jakarta |
| P1 | Isochrone walk + transit sebagai tool eksplorasi lokasi |
| P1 | Mobil (+ motor di compare card) dengan disclaimer no live traffic |
| P2 | Coverage analysis, multi-origin, Bodetabek, major cities |
| Post-MVP | Portfolio impact, urban planning community, full Indonesia |

---

## 3. Target User

**Primary:**
- Warga kota besar yang mencari kos/rumah/kantor (millennial & gen Z).
- Pekerja hybrid / commuter.

**Secondary (post-MVP):**
- Perencana kota, urban planner, akademisi.
- Pemda / Dishub / Bappeda.
- Developer properti.

**Jobs-to-be-done (JTBD):**
1. *"Kos di sini commute ke kantor berapa menit, naik apa?"* → A→B compare
2. *"Dari sini 15 menit jalan kaki bisa kemana aja?"* → walk isochrone
3. *"Area mana yang transit-nya bagus?"* → transit isochrone + coverage (later)

---

## 4. Geographic Rollout

Niat **full Indonesia**, rollout bertahap berdasarkan ketersediaan data GTFS/OSM:

| Tier | Wilayah | Prioritas | Catatan data |
|------|---------|-----------|--------------|
| T1 | **DKI Jakarta** | P0 — launch | TransJakarta GTFS resmi, GIS Pemprov, OSM padat |
| T2 | **Bodetabek** (Depok, Bekasi, Tangerang, Bogor) | P1 | GTFS Bogor (Pemkot), KRL coverage, TransJabodetabek |
| T3 | **Major cities** (Bandung, Surabaya, Yogyakarta, Semarang, Medan, Bali) | P2 | GTFS sporadis; perlu kurasi per kota |
| T4 | **Minor cities** | P3 | OSM walk/car only + approximated transit fallback |

**Guard behavior:** Request di luar bbox tier aktif → banner *"Belum tersedia di area ini"* + disable transit (jangan error 500).

---

## 5. Core Features

### 5.1 Optimal Commute Mode (A → B) — **HERO**

User set **titik A** (rumah/kos) dan **titik B** (sekolah/kantor).

Sistem hitung & bandingkan moda relevan, rekomendasikan **moda tercepat**:

| Moda | Phase | Output |
|------|-------|--------|
| Walking | P0 | Durasi, jarak |
| Walking + Transit | P0 | Durasi, transfer count, legs (TJ → MRT → KRL), estimasi biaya |
| Mobil | P1 | Durasi, jarak — **disclaimer: tanpa traffic real-time** |
| Motor | P1 | Durasi — **hanya di compare card**, bukan isochrone slider |

**Default departure:** Senin–Jumat 07:30 WIB (peak commute). User bisa ubah nanti (post-MVP).

**UI behavior:**
- Default landing mode = **Commute** (bukan Isochrone)
- Pin A (hijau) + pin B (merah); tombol swap A↔B
- Comparison cards: moda | waktu | biaya | transfer
- Badge **"Paling cepat"** pada moda optimal
- Expandable step-by-step directions untuk transit
- Note *"Selisih tipis"* jika top-2 moda beda <5 menit
- Transit route polyline di map saat card di-expand

**Acceptance criteria (MVP done when):**
- [ ] A→B di bbox Jakarta return ≥2 moda (walk + transit)
- [ ] `fastest_mode` benar untuk 5 fixture pairs (unit test)
- [ ] Response <5 detik uncached, <1 detik cached
- [ ] Transit legs show agency + line + board/alight stop
- [ ] UI render comparison tanpa reload full page

---

### 5.2 Single Point Isochrone — **Secondary**

- User input titik (alamat / klik map / pin).
- Mode (prioritas rollout):
  1. **Walking** (P0)
  2. **Walking + Public Transit** (P0)
  3. **Mobil** (P1) — isochrone slider only; motor **tidak** punya slider terpisah
- Slider waktu: 10 / 15 / 30 / 45 / 60 menit.
- Polygon di map.

**Acceptance criteria:**
- [ ] Walk isochrone Monas 15 menit render <3 detik
- [ ] Transit isochrone area ≥ walk isochrone same point/time (sanity)
- [ ] Cached repeat request <500ms

---

### 5.3 Multi-Origin Isochrone — Phase 4

- Halte/stasiun dalam radius 500m–1km → union isochrone + heatmap.
- Cap 20 origin (perf).

---

### 5.4 Transit Coverage Analysis — Phase 4

- % grid points reachable in ≤15 min transit per kecamatan.
- Precompute nightly untuk T1.

---

### 5.5 Insight — Post-MVP

- **Rule-based only** (bukan LLM): coverage score rendah/sedang/tinggi, selisih moda tipis.
- Contoh: *"Coverage transit rendah — pertimbangkan area lebih dekat halte."*

---

## 6. Strategic Decisions (from review)

| Decision | Choice | Alasan |
|----------|--------|--------|
| Hero UX | A→B compare first | Pain point harian user; isochrone = supporting |
| Transit before car | Walk+transit P0, car P1 | Differentiator; car tanpa traffic kurang akurat |
| GTFS KRL/MRT | **Kurasi manual, jangan build converter framework** | Risk #1 = data, bukan code; merge script one-off OK |
| GTFS order | TransJakarta resmi → Comuline KRL → GIS DPMPTSP MRT/LRT | Resmi dulu, community fill gap |
| Street routing | **Valhalla self-host only** | Public OSRM demo rate-limited, tidak production-ready |
| OSRM | Self-host optional later | Bukan default; Valhalla cukup multimodal street |
| Motor | Compare card only di MVP | Same Valhalla graph, effort minimal |
| AI / privacy / monetization | Deferred | Rule-based + works best dulu |
| Auth | None di MVP | Anonymous, no account |
| Share | URL encode A/B coords (post hero) | Viral loop; belum P0 |
| Frontend framework | **TanStack Start** + shadcn/ui + Tailwind | Bukan wajib technically — lihat §8.1; preset shadcn sudah siap |
| Runtime / PM | **Bun** | Fast install/dev; `bunx` untuk scaffold & shadcn CLI |
| UI kit | **shadcn/ui + Tailwind CSS v4** | Compare cards, slider, sheet mobile, toast — copy-paste components |
| Versioning | **SemVer** + `docs/changelog.md` | Pola [hesoyam](https://github.com/anggiedimasta/hesoyam): `release-sync.mjs` + Husky |
| Git hooks | **Husky** pre-commit + pre-push | pre-commit = Biome staged; pre-push = changelog + patch bump |

---

## 7. Data Sources (validated via web research)

### 7.1 Official / Semi-official

| Data | Provider | URL / ID | Status | Catatan |
|------|----------|----------|--------|---------|
| TransJakarta GTFS | PT Transportasi Jakarta | https://gtfs.transjakarta.co.id/files/file_gtfs.zip | ✅ Aktif | 253 rute, ~7.900 stop; update ~bulanan |
| TransJakarta (mirror) | Transitland | Onestop ID `f-transjakarta~id` | ✅ Aktif | Arsip historis 79 versi |
| Bogor Bus GTFS | Pemkot Bogor | [busmaps.com](https://busmaps.com/en/indonesia/Pemerintah-Kota-Bogor/sariksma-bogor) | ✅ Aktif | 30 rute, 304 stop |
| Titik transportasi umum | DPMPTSP DKI | [ArcGIS FeatureServer](https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/Hosted/Titik_Transportasi_Umum_Jakarta_v3/FeatureServer) | ✅ Aktif | MRT, LRT, LRT Jabodebek coords |
| Rute KRL (geometry) | GIS DKI | [ArcGIS MapServer](https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/Transportasi_Medan_Merdeka/MapServer/9) | ✅ Aktif | Polyline referensi, bukan schedule |

### 7.2 Community-maintained (KRL/MRT — no official GTFS)

| Data | Provider | URL | Status | Catatan |
|------|----------|-----|--------|---------|
| KRL schedule & infra | Comuline API | https://www.api.comuline.com/docs | ✅ Aktif | Scrape harian PT KAI; Jakarta + Yogyakarta |
| MRT Jakarta schedule | mrt-jakarta-api | https://mrt-jakarta-api-production.up.railway.app/v1 | ⚠️ Community | Scrape jakartamrt.co.id; jangan hard-depend tanpa fallback |
| KRL fare reference | api-partner.krl.co.id | via apps tarif-krl | ⚠️ Unofficial | Static fare table backup di repo |

### 7.3 Street network & routing

| Data | Provider | URL | Use case |
|------|----------|-----|----------|
| OSM Java extract | Geofabrik | https://download.geofabrik.de/asia/indonesia/java-latest.osm.pbf | T1–T2 routing |
| Transit routing | r5py (Conveyal R5) | https://r5py.readthedocs.io | Transit isochrone + A→B |
| MOTIS | motis-project | https://github.com/motis-project/motis | Fallback jika r5py bottleneck |
| Walk/car/motor | **Valhalla self-host** | https://github.com/valhalla/valhalla | `pedestrian`, `auto`, `motorcycle` |
| Map tiles | OpenFreeMap / Protomaps / self-host | TBD | Jangan hard-depend Mapbox paid tier |

### 7.4 Aggregators & fallback (T3–T4)

| Data | Provider | URL |
|------|----------|-----|
| Indonesia GTFS index | busmaps.com | https://busmaps.com/en/indonesia/feedlist |
| Mobility Database | mobilitydata.org | https://mobilitydata.org |
| Transitland | transit.land | https://www.transit.land |
| Approximated transit | CommuteTimeMap | https://commutetimemap.com |

### 7.5 NOT in MVP

- Live traffic (TomTom, Google, Waze)
- GTFS-RT / real-time delays
- Crowdsource reports
- Public OSRM demo endpoint

### 7.6 Data pipeline (T1 Jakarta)

```
1. Download TransJakarta GTFS (resmi) — jangan modifikasi schedule
2. Fetch Comuline KRL → append stops/trips (script one-off, bukan framework)
3. Fetch GIS DPMPTSP MRT/LRT coords → append ke stops.txt
4. Dedup stops within 50m; tag data_quality: official | community
5. Output: data/gtfs/jakarta-merged.zip
6. OSM: java-latest.osm.pbf
7. r5py network build (transit) + Valhalla graph build (street)
8. Weekly cron: re-fetch TransJakarta + Comuline; alert if route count drops >10%
```

**Data freshness SLA (MVP):**
- TransJakarta: refresh weekly
- Comuline KRL: refresh daily (mirror cron)
- OSM: refresh monthly
- Stale banner jika feed >14 hari tanpa update

---

## 8. Tech Stack

| Layer | Choice | Alasan |
|-------|--------|--------|
| Runtime / PM | **Bun** | Install & dev cepat; satu tool untuk JS/TS scripts |
| Frontend | **TanStack Start** (React) + MapLibre GL JS | File routing, type-safe URLs, SSR landing |
| UI | **shadcn/ui + Tailwind CSS v4** | Accessible components; dark mode via CSS vars |
| Backend | **Python FastAPI** | r5py, GeoPandas, GTFS tooling; **Go tidak perlu** |
| Lint/Format | **Biome** | TS/TSX/JSON; ESLint tidak dipakai |
| Database | PostgreSQL + PostGIS | Stops, cache isochrone/compare results |
| Transit | r5py (primary) | Isochrone + A→B multimodal |
| Street | Valhalla self-host (Railway/Fly) | Walk, car, motor; no public demo |
| Tests | Vitest + Testing Library (React) + pytest + Playwright | Critical path coverage |
| Git hooks | **Husky** | pre-commit (Biome) + pre-push (release-sync) |
| Versioning | **SemVer** + Keep a Changelog | Auto patch bump on push; lihat §18 |
| Hosting | Cloudflare / Railway (web + API) | TanStack Start SSR + FastAPI; ~$20–50/bulan |

### 8.1 Perlu TanStack Start?

**Tidak wajib.** Backend sudah FastAPI terpisah — core app = client-side map + API calls. Alternatif lebih ringan: **Vite + React SPA** + shadcn (`--template vite`).

**Pakai TanStack Start kalau:**
- Mau **share URL** type-safe (`/commute?a=…&b=…`) via TanStack Router
- Mau **SSR** untuk landing page / SEO portfolio
- Sudah punya **shadcn preset** — satu command scaffold

**Skip TanStack Start kalau:**
- Mau minim complexity; map app 99% client-side
- Khawatir Start belum stable (pre-1.0, breaking changes possible)

**Keputusan MVP:** **Pakai TanStack Start** — preset sudah ready, Router cocok untuk share link & mode toggle (Commute / Isochrone). Server functions **tidak dipakai**; semua routing logic tetap di FastAPI.

### 8.2 Project scaffold

```bash
# dari root monorepo, scaffold web app
cd apps
bunx --bun shadcn@latest init --preset b3bEeu7Soq --template start

# setelah init, tambah components MVP
bunx --bun shadcn@latest add button card badge slider sheet toast tabs input
```

**Struktur monorepo target:**
```
apps/
  web/          # TanStack Start + shadcn + MapLibre
  api/          # Python FastAPI
packages/
  shared/       # TS types shared (API response shapes)
```

**shadcn components MVP:**
- `card` — mode comparison
- `badge` — "Paling cepat"
- `slider` — isochrone minutes
- `sheet` — mobile compare panel
- `toast` — errors
- `tabs` — Commute / Isochrone toggle
- `input` — geocode search

**MapLibre:** install manual (`maplibre-gl`) — render di client component, jangan SSR map canvas.

### 8.3 Bun vs Python boundary

| Tool | Runtime |
|------|---------|
| `apps/web` dev/build/test | **Bun** |
| `apps/api` + r5py + ETL scripts | **Python 3.12+** (uv/pip) |
| shadcn CLI, Biome, Vitest | **Bun** |

Bun **tidak** replace Python backend — hanya frontend toolchain.

### 8.4 App version di UI

Inject semver dari `apps/web/package.json` ke bundle (pola hesoyam):

```ts
// vite / TanStack Start define
declare const __APP_PACKAGE_VERSION__: string;
export const APP_VERSION = __APP_PACKAGE_VERSION__;
```

Tampilkan `v{APP_VERSION}` di footer / settings — debug & portfolio credibility.

---

## 18. Versioning & Git Hooks

> Adapted from **[hesoyam](https://github.com/anggiedimasta/hesoyam)** — same maintainer toolchain.

### 18.1 SemVer & changelog

| Artifact | Path | Role |
|----------|------|------|
| Root version | `package.json` `"version"` | Monorepo semver source of truth |
| Web version | `apps/web/package.json` `"version"` | Synced on release cut |
| Changelog | `docs/changelog.md` | [Keep a Changelog](https://keepachangelog.com/); auto-sync block |
| Release script | `scripts/release-sync.mjs` | Parse conventional commits → changelog + bump |

**Starting version:** `0.1.0` (pre-release MVP).

**Commit format:** [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `chore:`, `docs:`, `test:` dengan scope opsional:

```
feat(web): A→B compare cards
fix(api): isochrone cache key collision
docs: update GTFS sources
```

Changelog sync markers (jangan edit manual di dalam block):

```markdown
## [Unreleased]

<!-- changelog:sync-begin -->
<!-- changelog:sync-end -->
```

### 18.2 Husky hooks

**Install:** `husky` devDependency + `"postinstall": "husky"` di root `package.json`.

#### pre-commit — lint staged files

```sh
# .husky/pre-commit
#!/usr/bin/env sh
set -e
bun run lint:staged
```

```json
// package.json scripts
"lint": "biome check .",
"lint:staged": "biome check --staged --write --no-errors-on-unmatched",
"format": "biome format --write ."
```

**Behavior:** Commit ditolak kalau Biome error pada staged TS/TSX/JSON. Full test suite tetap di CI (pre-commit tidak run pytest — terlalu lambat).

**Biome + shadcn:** Jangan `biome check --write` pada seluruh `components/ui/` sekaligus — organize-imports bisa break radix. Scoped check atau `biome-ignore` per file generated (lihat hesoyam AGENTS.md).

#### pre-push — changelog + patch bump

```sh
# .husky/pre-push
#!/usr/bin/env sh
set -e
node scripts/release-sync.mjs --if-needed
```

**Behavior (sama hesoyam):**
1. Ambil commits di `@{u}..HEAD`
2. Render ke `docs/changelog.md` `[Unreleased]`
3. Bump **patch** semver (`0.1.0` → `0.1.1`)
4. Promote `[Unreleased]` → `## [0.1.1] - YYYY-MM-DD`
5. Commit `chore(release): v0.1.1 changelog sync` dengan `HUSKY=0`
6. **Exit 1** — push diblock; user run `git push` lagi

**Skip loop:** Commit subject `chore(release):` di-skip hook; changelog sudah link commit → skip duplicate bump.

### 18.3 Release scripts (root package.json)

```json
{
  "scripts": {
    "postinstall": "husky",
    "lint": "biome check .",
    "lint:staged": "biome check --staged --write --no-errors-on-unmatched",
    "format": "biome format --write .",
    "changelog:sync": "node scripts/release-sync.mjs",
    "changelog:rebuild": "node scripts/release-sync.mjs --rebuild-recent",
    "release:cut": "node scripts/release-sync.mjs --release"
  },
  "devDependencies": {
    "husky": "^9.1.7"
  }
}
```

| Command | When |
|---------|------|
| `bun run changelog:sync` | Refresh `[Unreleased]` tanpa bump (manual) |
| `bun run release:cut` | Cut release + bump patch (manual, tanpa push) |
| pre-push `--if-needed` | Otomatis saat `git push` |

### 18.4 release-sync.mjs adaptasi

Copy dari `hesoyam/scripts/release-sync.mjs`, ubah paths:

| hesoyam | 15menit |
|---------|---------|
| `apps/web/package.json` | same |
| `package.json` (root) | same |
| `docs/changelog.md` | same |
| commitUrlBase default repo | `github.com/…/15menit` |

Optional later: sync `apps/api/pyproject.toml` version — tidak wajib MVP.

### 18.5 CI vs hooks

| Check | pre-commit | pre-push | GitHub Actions |
|-------|------------|----------|----------------|
| Biome (staged) | ✅ | — | ✅ full repo |
| Vitest | — | — | ✅ |
| pytest | — | — | ✅ |
| Changelog + bump | — | ✅ | — |

---

## 9. Moda Transportasi

| Moda | Phase | Engine | UI surface |
|------|-------|--------|------------|
| Walking | P0 | Valhalla / r5py | Compare + isochrone |
| Walking + Transit | P0 | r5py | Compare + isochrone |
| Mobil | P1 | Valhalla `auto` | Compare + isochrone; disclaimer wajib |
| Motor | P1 | Valhalla `motorcycle` | **Compare card only** |

**Copy disclaimer (mobil/motor):** *"Estimasi berdasarkan batas kecepatan jalan, belum termasuk traffic real-time."*

---

## 10. Non-Functional Requirements

- Mobile-first responsive (PWA phase 7).
- A→B compare <5 detik uncached.
- Isochrone <3 detik uncached.
- Bahasa Indonesia.
- Dark mode.
- Biome + pytest + vitest (Bun) in CI; **Biome juga di pre-commit (staged)**.
- API rate limit: 30 req/min/IP (abuse guard, no auth).

**Error states (minimum):**
- Outside bbox → banner, disable action
- Routing fail → toast + retry
- No transit path → show walk + car only, note *"Rute transit tidak ditemukan"*
- Data stale → yellow banner dengan `feed_updated_at`

**Deferred:** privacy policy, GDPR, monetization, user accounts.

---

## 11. Success Metrics (MVP)

| Metric | Target |
|--------|--------|
| Hero demo | Video 2 menit A→B + isochrone, Jakarta |
| A→B moda | Walk + transit + (optional car) compare works |
| Fixture tests | 5 known pairs pass fastest_mode assertion |
| Post-launch | 500 isochrone/compare per minggu |
| Portfolio | README + demo link + architecture diagram |

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **KRL/MRT no official GTFS** | Transit routing incomplete | Comuline + GIS DPMPTSP; ship TJ-only first if blocked; document gaps |
| mrt-jakarta-api down | MRT legs missing | Static MRT schedule fallback table in repo |
| r5py build slow/heavy | Dev friction | Cache built network; document build once; eval MOTIS |
| Valhalla RAM on Railway | OOM on Java extract | Use smaller bbox clip Jakarta first |
| Car without traffic | User distrust mobil ETA | Disclaimer + deprioritize vs transit |
| GTFS stale | Wrong schedules | Weekly refresh + staleness banner |
| Scope creep | Never ship | Hero = A→B only until Sprint 4 done |

**Biggest risk:** Data KRL/MRT — bukan tech stack. Alokasi waktu dev: **~40% data pipeline, ~30% routing, ~30% UI**.

---

## 13. Out of Scope (MVP)

- Live traffic
- LLM / AI insight
- Multi-pin comparison (3+ lokasi)
- PDF export
- Pemda dashboard
- Monetization & auth
- Privacy compliance formal
- Motor isochrone slider
- Public OSRM dependency

---

## 14. Known Gaps (belum didefinisi — resolve saat implement)

| Gap | Status | Rekomendasi |
|-----|--------|-------------|
| Map tile provider final | Open | OpenFreeMap atau Protomap free tier; decide Sprint 1 |
| TanStack Start stability | Accepted | Pre-1.0; pin versions; no server functions MVP |
| MapLibre + SSR | Open | Dynamic import `ssr: false` untuk map component |
| Share URL format | Open | `?a=lat,lng&b=lat,lng&mode=commute` — Sprint 4 |
| Departure time picker UI | Open | Hardcode 07:30 WIB MVP; picker post-MVP |
| Angkot / mikrolet | Out of scope T1 | Tidak ada GTFS; mention in FAQ |
| First-time onboarding tooltip | Open | 1-screen "Pin rumah → Pin kantor → Bandingkan" |
| Infra cost ceiling | Open | Cap $50/bulan MVP; monitor Valhalla RAM |
| Accessibility (a11y) | Low priority | Keyboard pin drop post-MVP |
| SEO / landing page copy | Open | Sprint 5 |
| Fixture pairs for QA | Open | Define 5 pairs in `data/fixtures/commute-pairs.json` Sprint 3 |
| LRT Jabodebek schedule | Gap in data | GIS coords only MVP; schedule later |

---

## 15. Competitive Position

| | Moovit / Google | 15menit |
|--|-----------------|---------|
| Core job | Navigate now | Decide where to live/work |
| Isochrone | ❌ | ✅ |
| Mode comparison card | Partial | ✅ side-by-side |
| Indonesia-first housing angle | ❌ | ✅ |
| Offline / free OSS stack | ❌ | ✅ |

---

## 16. Tagline Options

- "Commute pintar: moda mana paling cepat?" ← **primary for hero**
- "Cari tempat tinggal berdasarkan waktu, bukan jarak."
- "Tau dalam 15 menit ke mana aja lo bisa nyampe."
- "Peta Aksesibilitas Transportasi Indonesia"

---

## 17. Related Docs

- [Backlog](./backlog.md) — phased todos (Flow · Data · Behavior · Tests · Status)
- [changelog](./changelog.md) — release history (auto-synced)
- [Artifact format](./artifact_format.md) — doc conventions (pola hesoyam)
