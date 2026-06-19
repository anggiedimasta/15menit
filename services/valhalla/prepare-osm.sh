#!/usr/bin/env bash
# Clip Geofabrik Java extract to Jabodetabek bbox before Valhalla tile build.
# Matches apps/api/app/config.py bodetabek_bbox: (-6.75, 106.3, -6.0, 107.2)

set -euo pipefail

CUSTOM="${CUSTOM_FILES:-/custom_files}"
cd "${CUSTOM}"

CLIP="jakarta-bodetabek.osm.pbf"
JAVA="java-latest.osm.pbf"
JAVA_URL="${JAVA_SOURCE_URL:-https://download.geofabrik.de/asia/indonesia/java-latest.osm.pbf}"
# osmium extract -b: west,south,east,north
BBOX="${OSM_CLIP_BBOX:-106.3,-6.75,107.2,-6.0}"

TILE_TAR="${CUSTOM}/valhalla_tiles.tar"
TILE_DIR="${CUSTOM}/valhalla_tiles"

if [[ -f "${TILE_TAR}" ]] || [[ -n "$(ls -A "${TILE_DIR}" 2>/dev/null || true)" ]]; then
  echo "INFO: Existing Valhalla tiles found — skipping OSM prepare."
  exit 0
fi

if [[ -f "${CLIP}" ]]; then
  echo "INFO: Clipped OSM already at ${CLIP}"
  exit 0
fi

echo "INFO: Preparing Jabodetabek OSM clip (first deploy: download + clip + tile build)..."

if [[ ! -f "${JAVA}" ]]; then
  echo "INFO: Downloading Java OSM extract from ${JAVA_URL} ..."
  curl -fsSL "${JAVA_URL}" -o "${JAVA}"
fi

echo "INFO: Clipping to bbox ${BBOX} ..."
osmium extract -b "${BBOX}" "${JAVA}" -o "${CLIP}" --overwrite

echo "INFO: Removing full Java extract to save disk on volume ..."
rm -f "${JAVA}"

echo "INFO: OSM ready at ${CUSTOM}/${CLIP}"
