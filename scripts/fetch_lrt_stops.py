#!/usr/bin/env python3
"""Fetch LRT Jakarta + LRT Jabodebek stop coords from GIS DPMPTSP ArcGIS."""

from __future__ import annotations

import argparse
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

STATIC_PATH = Path("data/gtfs/static/lrt_stops.json")
FEATURE_SERVER = (
    "https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/"
    "Hosted/Titik_Transportasi_Umum_Jakarta_v3/FeatureServer/26/query"
)
# ArcGIS rejects compound NOT LIKE; STASIUN LRT excludes TJ halte named *LRT*.
LRT_WHERE = "fungsi LIKE '%STASIUN LRT%'"
JABODEBEK_HINTS = (
    "jabodebek",
    "bekasi",
    "cibubur",
    "cikoko",
    "halim",
    "dukuh atas 2",
    "jati",
    "setiabudi",
    "kuningan",
    "rasuna",
    "cawang",
    "tmii",
    "harjamukti",
)


def load_static() -> list[dict[str, object]]:
    return json.loads(STATIC_PATH.read_text(encoding="utf-8"))


def _slug(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", name.upper()).strip("-")
    return cleaned[:12] or "LRT"


def _clean_stop_name(raw: str) -> str:
    name = raw.strip()
    for prefix in ("STASIUN LRT ST.", "STASIUN LRT", "ST. "):
        if name.upper().startswith(prefix.upper()):
            name = name[len(prefix) :].strip()
            break
    return name.title() if name.isupper() else name


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _merge_static_jakarta(stops: list[dict[str, object]]) -> list[dict[str, object]]:
    """ArcGIS layer is Jabodebek-heavy; add static Jakarta LRT not within 50m."""
    merged = list(stops)
    seen_ids = {str(s["stop_id"]) for s in merged}
    for row in load_static():
        if row.get("line", "LRT-JKT") != "LRT-JKT":
            continue
        lat, lng = float(row["lat"]), float(row["lng"])
        if any(_haversine_m(lat, lng, float(s["lat"]), float(s["lng"])) <= 50 for s in merged):
            continue
        stop_id = str(row["stop_id"])
        if stop_id in seen_ids:
            continue
        merged.append(dict(row))
        seen_ids.add(stop_id)
    return merged


def _classify_line(name: str, fungsi: str, lat: float, lng: float) -> str:
    fungsi_lower = fungsi.lower()
    if "jabodebek" in fungsi_lower:
        return "LRT-JBD"
    lowered = name.lower()
    if any(hint in lowered for hint in JABODEBEK_HINTS):
        return "LRT-JBD"
    if lng > 106.88 or lat < -6.25:
        return "LRT-JBD"
    return "LRT-JKT"


def fetch_arcgis() -> list[dict[str, object]] | None:
    params = urllib.parse.urlencode(
        {
            "where": LRT_WHERE,
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
        lat_f, lng_f = float(lat), float(lng)
        fungsi = str(attrs.get("fungsi") or "")
        display_name = _clean_stop_name(name)
        key = re.sub(r"\s+", " ", display_name.upper())
        line = _classify_line(display_name, fungsi, lat_f, lng_f)
        stop_id = f"LRT-{_slug(display_name)}"
        stops[key] = {
            "stop_id": stop_id,
            "name": display_name,
            "lat": lat_f,
            "lng": lng_f,
            "line": line,
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
    else:
        extra = _merge_static_jakarta(stops)
        if len(extra) > len(stops):
            stops = extra
            source = "arcgis+static-jakarta"

    out_path.write_text(json.dumps(stops, indent=2), encoding="utf-8")
    meta = out_path.with_suffix(".meta.txt")
    meta.write_text(
        f"fetched_at={datetime.now(UTC).isoformat()}\nsource={source}\nstops={len(stops)}\n",
        encoding="utf-8",
    )
    print(f"Saved {len(stops)} LRT stops ({source}) -> {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/gtfs/lrt_stops.json")
    args = parser.parse_args()
    fetch(Path(args.out))
