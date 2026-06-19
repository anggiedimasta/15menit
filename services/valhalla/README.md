# Valhalla on Railway

OSM routing engine for 15menit production isochrones.

- **Image base:** [gis-ops/docker-valhalla](https://github.com/gis-ops/docker-valhalla)
- **OSM:** Geofabrik Java → clip **Jabodetabek only** (not full Java on disk)
- **Volume:** `/custom_files` — **4096 MB max** (Hobby plan limit 5000 MB)
- **Port:** 8002, health `GET /status`
- **First deploy:** 15–30 min graph build; scale RAM ≥ 4 GB
- **Coverage:** Jabodetabek bbox (Jakarta metro)

API connects via `VALHALLA_URL=http://${{valhalla.RAILWAY_PRIVATE_DOMAIN}}:8002`.
