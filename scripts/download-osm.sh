#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT/data/osm"
FILE="$OUT_DIR/java-latest.osm.pbf"
URL="https://download.geofabrik.de/asia/indonesia/java-latest.osm.pbf"
MD5_URL="https://download.geofabrik.de/asia/indonesia/java-latest.osm.pbf.md5"

mkdir -p "$OUT_DIR"

if [[ -f "$FILE" ]]; then
  echo "Existing file: $FILE ($(du -h "$FILE" | cut -f1))"
  if command -v md5sum >/dev/null 2>&1; then
    REMOTE_MD5=$(curl -fsSL "$MD5_URL" | awk '{print $1}')
    LOCAL_MD5=$(md5sum "$FILE" | awk '{print $1}')
    if [[ "$REMOTE_MD5" == "$LOCAL_MD5" ]]; then
      echo "Checksum match — skip download"
      exit 0
    fi
  fi
fi

echo "Downloading $URL ..."
curl -fL --progress-bar -o "$FILE" "$URL"
echo "Saved $(du -h "$FILE" | cut -f1) at $(date -Iseconds)"
