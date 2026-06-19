#!/usr/bin/env bash
# Clip Geofabrik Java extract to Jabodetabek bbox before Valhalla tile build.
# Matches apps/api/app/config.py bodetabek_bbox: (-6.75, 106.3, -6.0, 107.2)
# Railway hobby plan: persistent volume max 5000 MB — use 4096 MB for headroom.

set -euo pipefail

CUSTOM="${CUSTOM_FILES:-/custom_files}"
cd "${CUSTOM}"

CLIP="jakarta-bodetabek.osm.pbf"
JAVA="java-latest.osm.pbf"
# Direct clip URL (optional): skip Java download when OSM_CLIP_URL points to a pre-clipped PBF.
OSM_CLIP_URL="${OSM_CLIP_URL:-}"
JAVA_URL="${JAVA_SOURCE_URL:-https://download.geofabrik.de/asia/indonesia/java-latest.osm.pbf}"
# osmium extract -b: west,south,east,north
BBOX="${OSM_CLIP_BBOX:-106.3,-6.75,107.2,-6.0}"

TILE_TAR="${CUSTOM}/valhalla_tiles.tar"
TILE_DIR="${CUSTOM}/valhalla_tiles"

if [[ -f "${TILE_TAR}" ]]; then
  echo "INFO: Existing Valhalla tile archive found — skipping OSM prepare."
  exit 0
fi

if [[ -d "${TILE_DIR}" ]] && [[ -n "$(ls -A "${TILE_DIR}" 2>/dev/null || true)" ]]; then
  echo "WARN: Incomplete valhalla_tiles directory (no archive) — removing for rebuild."
  rm -rf "${TILE_DIR}"
fi

if [[ -f "${CLIP}" ]]; then
  echo "INFO: Clipped OSM already at ${CLIP}"
  exit 0
fi

echo "INFO: Preparing Jabodetabek OSM clip (first deploy: download + clip + tile build)..."

if [[ -n "${OSM_CLIP_URL}" ]]; then
  echo "INFO: Downloading pre-clipped OSM from ${OSM_CLIP_URL} ..."
  curl -fsSL "${OSM_CLIP_URL}" -o "${CLIP}"
elif [[ ! -f "${JAVA}" ]]; then
  echo "INFO: Downloading Java OSM extract from ${JAVA_URL} (~150 MB) ..."
  curl -fsSL "${JAVA_URL}" -o "${JAVA}"
  echo "INFO: Clipping to bbox ${BBOX} ..."
  osmium extract -b "${BBOX}" "${JAVA}" -o "${CLIP}" --overwrite
  echo "INFO: Removing full Java extract to save disk on volume ..."
  rm -f "${JAVA}"
else
  echo "INFO: Clipping to bbox ${BBOX} ..."
  osmium extract -b "${BBOX}" "${JAVA}" -o "${CLIP}" --overwrite
  rm -f "${JAVA}"
fi

echo "INFO: OSM ready at ${CUSTOM}/${CLIP}"
