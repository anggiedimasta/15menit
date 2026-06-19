#!/usr/bin/env bash
set -euo pipefail

/valhalla/scripts/prepare-osm.sh

export build_elevation="${build_elevation:-False}"
export serve_tiles="${serve_tiles:-True}"
export use_tiles_ignore_pbf="${use_tiles_ignore_pbf:-True}"
export build_tar="${build_tar:-True}"
export build_admins="${build_admins:-False}"
export build_time_zones="${build_time_zones:-False}"

# Prefer clipped local PBF in /custom_files over remote tile_urls.
unset tile_urls

exec /valhalla/scripts/run.sh "$@"
