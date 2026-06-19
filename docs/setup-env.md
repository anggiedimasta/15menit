# Setup Environment — 15menit

Panduan langkah demi langkah untuk menjalankan 15menit secara lokal dengan data nyata (Valhalla, Nominatim, GTFS transit) dan cache opsional (PostGIS / Supabase).

## Prasyarat

- [Bun](https://bun.sh) ≥ 1.1
- [Python](https://www.python.org/) ≥ 3.11 + `pip`
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (untuk PostGIS & Valhalla)
- Akun [Supabase](https://supabase.com/) (opsional, untuk cache geocode)

---

## Docker Desktop (Windows)

1. **Install** [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) (WSL 2 backend disarankan).
2. **Start** Docker Desktop dari Start Menu — tunggu ikon whale di system tray berhenti animasi (“Docker Desktop is running”).
3. **Verify** di PowerShell dari root repo:

```powershell
docker --version
docker compose version
docker info    # Server section harus muncul — bukan "Cannot connect"
docker ps      # kosong OK; error "daemon" = Desktop belum jalan
```

| Masalah Windows | Solusi |
|-----------------|--------|
| `error during connect` / daemon not running | Buka Docker Desktop; tunggu ~30s; retry `docker ps` |
| Port 5432 sudah dipakai | Stop Postgres lokal atau ubah port di `docker-compose.yml` |
| Valhalla lambat / OOM | Settings → Resources → RAM ≥ 8 GB; pertama kali build graph lama |
| Path volume | Repo di drive NTFS biasa (`C:\Users\...`) — hindari path network drive |

**Shortcut (PowerShell):**

```powershell
.\scripts\docker-up.ps1              # PostGIS + alembic
.\scripts\docker-up.ps1 -Routing     # + Valhalla (build pertama lama)
```

Setelah PostGIS jalan, pastikan `.env` punya `DATABASE_URL` seperti di `.env.example`.

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
| `ROUTING_MODE` | `auto` / `mock` / `valhalla` | Tidak (default `auto`) | `auto` = probe Valhalla di startup; `mock` = simulasi; `valhalla` = isochrone/rute OSM nyata |
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

Windows shortcut: `.\scripts\docker-up.ps1` (starts db + runs `alembic upgrade head`).

Terapkan migrasi cache (jika belum lewat script di atas):

```bash
cd apps/api && alembic upgrade head
```

> Alembic memakai driver `psycopg` v3 (`pip install -e ".[db]"`). `alembic/env.py` otomatis menulis ulang `postgresql://` → `postgresql+psycopg://`.

Atau gunakan skema Supabase: jalankan `supabase/migrations/001_cache.sql` di SQL Editor Supabase.

---

## 4. Setup Valhalla (isochrone jalan kaki & mobil)

Valhalla membutuhkan graph OSM — proses build bisa lama (±30–60 menit pertama kali).

```bash
docker compose --profile routing up -d valhalla
```

Set di `.env`:

```env
ROUTING_MODE=auto
VALHALLA_URL=http://localhost:8002
```

API otomatis memakai Valhalla jika `/status` merespons 200. Paksa simulasi dengan `ROUTING_MODE=mock`.

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
| Cache tidak jalan | `DATABASE_URL` benar + `alembic upgrade head` (butuh `pip install -e ".[db]"` di `apps/api`) |
| Env tidak terbaca API | Pastikan `.env` di **root** repo, bukan `apps/web/.env` |

---

## 9. Deploy ke Railway (production)

Monorepo ini punya **dua service** terpisah di satu Railway project:

| Service | Root directory | Config file | Start |
|---------|----------------|-------------|-------|
| **api** | `apps/api` | `/apps/api/railway.toml` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **web** | `/` (repo root) | `/railway.web.toml` | `bun run --cwd apps/web start` (TanStack Start + srvx) |

Project Railway: [15menit](https://railway.com/project/328787c9-7738-475f-aea4-89050cc4b6ba)

Repo GitHub: `https://github.com/anggiedimasta/15menit` — auto-deploy dari branch `main` setelah config di-push.

### 9.1 Variabel environment (Railway dashboard)

**API service** — set manual atau via Railway references:

| Variabel | Nilai production v1 | Wajib? |
|----------|---------------------|--------|
| `ROUTING_MODE` | `mock` | Ya (tanpa Valhalla) |
| `TRANSIT_MODE` | `mock` | Ya (tanpa GTFS bundle) |
| `ALLOWED_ORIGINS` | `https://${{web.RAILWAY_PUBLIC_DOMAIN}}` | Ya (CORS browser) |
| `DATABASE_URL` | dari Postgres plugin | Opsional |
| `SUPABASE_URL` / `VITE_SUPABASE_URL` | URL proyek Supabase | Opsional |
| `SUPABASE_SERVICE_ROLE` | service role key | Opsional (tulis cache) |

**Web service** — `VITE_*` dibaca saat **build**, bukan runtime:

| Variabel | Nilai | Wajib? |
|----------|-------|--------|
| `VITE_API_URL` | `https://${{api.RAILWAY_PUBLIC_DOMAIN}}` | Ya |
| `VITE_SUPABASE_URL` | URL proyek Supabase | Opsional |
| `VITE_SUPABASE_ANON_KEY` | publishable/anon key | Opsional |

> **Penting:** Set `VITE_API_URL` **sebelum** deploy web pertama (atau redeploy setelah API punya domain). Tanpa ini, production fallback ke `http://localhost:8000`.

> **Secrets:** Jangan commit `.env`. Set `SUPABASE_SERVICE_ROLE` hanya di API service.

### 9.2 Push config & deploy

```bash
git add apps/api/railway.toml apps/api/railpack.json railway.web.toml railpack.json apps/api/Procfile package.json apps/web/package.json apps/api/app/main.py docs/setup-env.md
git commit -m "chore: add Railway deploy config for api and web"
git push origin main
```

Railway akan rebuild otomatis. Cek status di project dashboard atau:

```bash
# via Railway CLI (opsional)
railway status --project 328787c9-7738-475f-aea4-89050cc4b6ba
```

### 9.3 Verifikasi

```bash
curl https://<api-domain>/health
# {"status":"ok"}

# Buka https://<web-domain> — health chip hijau jika API reachable
```

Valhalla dan GTFS **tidak** di-deploy di Railway v1; mock mode cukup untuk demo isochrone/commute.
