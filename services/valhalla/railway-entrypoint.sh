#!/usr/bin/env bash
set -euo pipefail

CUSTOM="${CUSTOM_FILES:-/custom_files}"
mkdir -p "${CUSTOM}" "${CUSTOM}/transit_tiles"
# Railway volumes mount as root; valhalla user needs write access for OSM download + tiles.
chown -R valhalla:valhalla "${CUSTOM}"

runuser -u valhalla -- /valhalla/scripts/prepare-osm.sh

export build_elevation="${build_elevation:-False}"
export serve_tiles="${serve_tiles:-True}"
# Rebuild from PBF until tile archive exists (avoids loading partial valhalla_tiles/).
if [[ -f "${CUSTOM}/valhalla_tiles.tar" ]]; then
  export use_tiles_ignore_pbf="${use_tiles_ignore_pbf:-True}"
else
  export use_tiles_ignore_pbf="False"
fi
export build_tar="${build_tar:-True}"
export build_admins="${build_admins:-False}"
export build_time_zones="${build_time_zones:-False}"

# Prefer clipped local PBF in /custom_files over remote tile_urls.
unset tile_urls

# docker-valhalla defaults server_threads to nproc; Railway hosts expose many cores
# and Valhalla opens tile files per worker → "Too many open files" at low ulimit.
# Force 2 — do not honor external server_threads (Railway/nproc may override cap).
export server_threads=2
ulimit -n 65536 2>/dev/null || ulimit -n 4096 2>/dev/null || true

# Railway healthchecks probe $PORT; default 8002 matches EXPOSE and API VALHALLA_URL.
LISTEN_PORT="${PORT:-8002}"
export PORT="${LISTEN_PORT}"

CONFIG="${CUSTOM}/valhalla.json"
if [[ -f "${CONFIG}" ]] && command -v jq >/dev/null 2>&1; then
  jq --argjson t 2 --arg listen "tcp://*:${LISTEN_PORT}" \
    '.mjolnir.concurrency = $t | .httpd.service.listen = $listen | del(.service)' \
    "${CONFIG}" > "${CONFIG}.railway.tmp" && mv "${CONFIG}.railway.tmp" "${CONFIG}"
fi

echo "INFO: Railway entrypoint forced server_threads=${server_threads} listen=tcp://*:${LISTEN_PORT} (PORT=${PORT})"
exec env server_threads="${server_threads}" /valhalla/scripts/run.sh "$@"
