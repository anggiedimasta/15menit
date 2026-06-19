#!/usr/bin/env python3
"""Fetch MRT Jakarta stop coords from GIS DPMPTSP ArcGIS with static fallback."""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

STATIC_PATH = Path("data/gtfs/static/mrt_stops.json")
FEATURE_SERVER = (
    "https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/"
    "Hosted/Titik_Transportasi_Umum_Jakarta_v3/FeatureServer/26/query"
)
MRT_WHERE = "fungsi LIKE '%STASIUN MRT%'"


def load_static() -> list[dict[str, object]]:
    return json.loads(STATIC_PATH.read_text(encoding="utf-8"))


def _slug(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", name.upper()).strip("-")
    return cleaned[:12] or "MRT"


def _clean_stop_name(raw: str) -> str:
    name = raw.strip()
    for prefix in ("STASIUN MRT ST.", "STASIUN MRT", "ST. "):
        if name.upper().startswith(prefix.upper()):
            name = name[len(prefix) :].strip()
            break
    return name.title() if name.isupper() else name


def fetch_arcgis() -> list[dict[str, object]] | None:
    params = urllib.parse.urlencode(
        {
            "where": MRT_WHERE,
            "outFields": "nama,lat,long,jenis,fungsi",
            "returnGeometry": "true",
            "f": "json",
            "resultRecordCount": 200,
        }
    )
    url = f"{FEATURE_SERVER}?{params}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "15menit/0.1 (GTFS pipeline)"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        return None

    stops: dict[str, dict[str, object]] = {}
    for feature in payload.get("features", []):
        attrs = feature.get("attributes", {})
        name = (attrs.get("nama") or "").strip()
        if not name:
            continue
        lat = attrs.get("lat")
        lng = attrs.get("long")
        geom = feature.get("geometry") or {}
        if lat is None:
            lat = geom.get("y")
        if lng is None:
            lng = geom.get("x")
        if lat is None or lng is None:
            continue
        key = re.sub(r"\s+", " ", _clean_stop_name(name).upper())
        stop_id = f"MRT-{_slug(_clean_stop_name(name))}"
        stops[key] = {
            "stop_id": stop_id,
            "name": _clean_stop_name(name),
            "lat": float(lat),
            "lng": float(lng),
        }

    rows = list(stops.values())
    return rows if len(rows) >= 3 else None


def fetch(out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    source = "arcgis"
    stops = fetch_arcgis()
    if not stops:
        source = "static"
        stops = load_static()

    out_path.write_text(json.dumps(stops, indent=2), encoding="utf-8")
    meta = out_path.with_suffix(".meta.txt")
    meta.write_text(
        f"fetched_at={datetime.now(UTC).isoformat()}\nsource={source}\nstops={len(stops)}\n",
        encoding="utf-8",
    )
    print(f"Saved {len(stops)} MRT stops ({source}) -> {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/gtfs/mrt_stops.json")
    args = parser.parse_args()
    fetch(Path(args.out))
