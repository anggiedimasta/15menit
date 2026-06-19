# Setup Environment — 15menit

Panduan langkah demi langkah untuk menjalankan 15menit secara lokal dengan data nyata (Valhalla, Nominatim, GTFS transit) dan cache opsional (PostGIS / Supabase).

## Prasyarat

- [Bun](https://bun.sh) ≥ 1.1
- [Python](https://www.python.org/) ≥ 3.11 + `pip`
- [Docker](https://www.docker.com/) + Docker Compose (untuk PostGIS & Valhalla)
- Akun [Supabase](https://supabase.com/) (opsional, untuk cache geocode)

---

## 1. Clone & install dependensi

```bash
git clone https://github.com/anggiedimasta/15menit.git
cd 15menit
bun install
cd apps/api && pip install -e ".[db]" && cd ../..
```

---

## 2. Salin file environment

```bash
cp .env.example .env
```

Edit **satu file** `.env` di root repo. API (python-dotenv) dan web (Vite `envDir`) sama-sama membaca file ini.

| Variabel | Contoh | Wajib? | Keterangan |
|----------|--------|--------|------------|
| `DATABASE_URL` | `postgresql://fifteenmenit:fifteenmenit@localhost:5432/fifteenmenit` | Ya (cache) | PostGIS lokal via Docker |
| `ROUTING_MODE` | `mock` / `valhalla` | Tidak (default `mock`) | `mock` = simulasi; `valhalla` = isochrone/rute OSM nyata |
| `TRANSIT_MODE` | `mock` / `gtfs` | Tidak (default `mock`) | `mock` = fixture; `gtfs` = data TransJakarta |
| `VALHALLA_URL` | `http://localhost:8002` | Jika `ROUTING_MODE=valhalla` | Endpoint Valhalla (Docker profile `routing`) |
| `GTFS_MERGED_PATH` | `data/gtfs/jakarta-merged.zip` | Jika `TRANSIT_MODE=gtfs` | Path GTFS setelah download |
| `VITE_API_URL` | `http://localhost:8000` | Tidak | URL FastAPI untuk frontend; **abaikan** di dev — Vite proxy `/api` → `:8000` |
| `VITE_SUPABASE_URL` | `https://xxxxx.supabase.co` | Opsional | Cache geocode (client read) |
| `VITE_SUPABASE_ANON_KEY` | `sb_publishable_*` atau anon JWT | Opsional | Publishable/anon key (read-only `geocode_cache`) |
| `SUPABASE_SERVICE_ROLE` | `eyJhbGciOi...` | Opsional | Tulis cache dari API — **jangan** expose ke web |
| `NOMINATIM_URL` | `https://nominatim.openstreetmap.org` | Tidak (default OSM) | Proxy geocode API |
| `CACHE_TTL_HOURS` | `24` | Tidak | TTL cache isochrone/geocode |
| `GEOCODE_RATE_LIMIT_PER_SEC` | `1` | Tidak | Rate limit proxy Nominatim |

> **Supabase URL:** Cukup set `VITE_SUPABASE_URL` sekali. API otomatis memakai nilai yang sama untuk tulis cache (fallback di `config.py`). Tidak perlu `SUPABASE_URL` terpisah.

> **Dev proxy:** Tanpa `VITE_API_URL`, `bun run dev` mem-proxy `/api` → `localhost:8000`.

---

## 3. Jalankan PostGIS (database)

```bash
docker compose up -d db
```

Terapkan migrasi cache:

```bash
cd apps/api && alembic upgrade head
```

Atau gunakan skema Supabase: jalankan `supabase/migrations/001_cache.sql` di SQL Editor Supabase.

---

## 4. Setup Valhalla (isochrone jalan kaki & mobil)

Valhalla membutuhkan graph OSM — proses build bisa lama (±30–60 menit pertama kali).

```bash
docker compose --profile routing up -d valhalla
```

Set di `.env`:

```env
ROUTING_MODE=valhalla
VALHALLA_URL=http://localhost:8002
```

Verifikasi:

```bash
curl http://localhost:8002/status
```

Tanpa Valhalla, biarkan `ROUTING_MODE=mock` — polygon isochrone tetap non-lingkaran (grid jalan) tapi bukan data OSM nyata.

---

## 5. Data GTFS transit (TransJakarta)

```bash
python scripts/download_gtfs.py
```

Set di `.env`:

```env
TRANSIT_MODE=gtfs
GTFS_MERGED_PATH=data/gtfs/jakarta-merged.zip
```

---

## 6. Setup Supabase (opsional — cache geocode)

### 6.1 Buat proyek

1. Buka [supabase.com/dashboard](https://supabase.com/dashboard)
2. **New project** → pilih region (Singapore disarankan)
3. Catat **Project URL** dan **publishable key** (atau legacy anon JWT)

### 6.2 Jalankan migrasi cache

Di **SQL Editor**, paste isi file `supabase/migrations/001_cache.sql` → **Run**.

Tabel yang dibuat:

- `geocode_cache` — hasil pencarian Nominatim
- `isochrone_cache` — polygon Valhalla (sama dengan TieredCache API via `DATABASE_URL`)

### 6.3 Isi `.env`

```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_xxxxxxxx
SUPABASE_SERVICE_ROLE=eyJhbGciOi...   # opsional — tulis cache dari API
```

> **Publishable key:** format `sb_publishable_*` menggantikan anon JWT untuk client read. REST headers (`apikey` + `Authorization: Bearer`) sama seperti anon key.

Frontend prefetch cache geocode jika tersedia; API mem-proxy Nominatim sebagai sumber utama dan menulis ke Supabase jika `SUPABASE_SERVICE_ROLE` diset.

---

## 7. Jalankan aplikasi

Terminal 1 — API:

```bash
bun run dev:api
```

Terminal 2 — Web:

```bash
bun run dev
```

Buka [http://localhost:3000](http://localhost:3000).

UI floating glass: peta full-screen, panel atas (Dari/Ke), chip bawah (Commute | Isochrone), hasil perbandingan moda di kartu bawah.

---

## 8. Verifikasi

```bash
bun run test:all      # vitest + pytest
bun run lint          # biome
bun run test:e2e      # Playwright (butuh dev server + API)
```

Health check manual:

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/geocode/search?q=Monas"
```

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| API tidak terhubungi | Pastikan `bun run dev:api` jalan; di dev, proxy `/api` aktif tanpa `VITE_API_URL` |
| Isochrone error | Valhalla belum siap → tunggu build atau pakai `ROUTING_MODE=mock` |
| Geocode kosong | Nominatim rate limit → tunggu 1 detik antar request |
| Transit tidak muncul | `TRANSIT_MODE=mock` atau GTFS belum didownload |
| Cache tidak jalan | `DATABASE_URL` benar + `alembic upgrade head` |
| Env tidak terbaca API | Pastikan `.env` di **root** repo, bukan `apps/web/.env` |
