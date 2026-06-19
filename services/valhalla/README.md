# Valhalla on Railway

OSM routing engine for 15menit production isochrones.

- **Image base:** [gis-ops/docker-valhalla](https://github.com/gis-ops/docker-valhalla)
- **OSM:** Geofabrik Java → clip Jabodetabek bbox before tile build
- **Volume:** `/custom_files` (tiles persist across redeploys)
- **Port:** 8002, health `GET /status`
- **First deploy:** 10–30 min graph build; scale RAM ≥ 4 GB on Pro plan

API connects via `VALHALLA_URL=http://${{valhalla.RAILWAY_PRIVATE_DOMAIN}}:8002`.
