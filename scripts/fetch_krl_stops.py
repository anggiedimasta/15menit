#!/usr/bin/env python3
"""Fetch KRL station list from Comuline API with static coord fallback."""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

STATIC_PATH = Path("data/gtfs/static/krl_stops.json")
COMULINE_URL = "https://api.comuline.com/v1/station"
MIN_STOPS = 10


def load_static() -> list[dict[str, object]]:
    return json.loads(STATIC_PATH.read_text(encoding="utf-8"))


def _normalize_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def _static_coord_index() -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    by_code: dict[str, dict[str, object]] = {}
    by_name: dict[str, dict[str, object]] = {}
    for row in load_static():
        stop_id = str(row.get("stop_id", ""))
        code = stop_id.split("-")[-1].upper() if "-" in stop_id else stop_id.upper()
        by_code[code] = row
        by_name[_normalize_name(str(row.get("name", "")))] = row
    return by_code, by_name


def _lookup_static_coords(
    station_id: str,
    name: str,
    by_code: dict[str, dict[str, object]],
    by_name: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    code = station_id.upper()
    if code in by_code:
        return by_code[code]
    normalized = _normalize_name(name)
    if normalized in by_name:
        return by_name[normalized]
    for key, row in by_name.items():
        if key.startswith(normalized) or normalized.startswith(key):
            return row
    return None


def fetch_comuline() -> list[dict[str, object]] | None:
    try:
        req = urllib.request.Request(
            COMULINE_URL,
            headers={"User-Agent": "15menit/0.1 (GTFS pipeline)"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        print(f"Comuline unavailable ({COMULINE_URL}: {exc}); using static fallback")
        return None

    rows = payload.get("data", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        print("Comuline response missing data[]; using static fallback")
        return None

    by_code, by_name = _static_coord_index()
    stops: list[dict[str, object]] = []
    seen: set[str] = set()

    for row in rows:
        if row.get("type") != "KRL":
            continue
        metadata = row.get("metadata") or {}
        if metadata.get("active") is False:
            continue
        origin = metadata.get("origin") or {}
        daop = origin.get("daop")
        if daop not in (None, 1):
            continue

        station_id = str(row.get("id") or "").upper()
        name = str(row.get("name") or "").strip()
        if not station_id or not name:
            continue

        static = _lookup_static_coords(station_id, name, by_code, by_name)
        if static is None:
            continue

        stop_id = f"KRL-{station_id}"
        if stop_id in seen:
            continue
        seen.add(stop_id)
        stops.append(
            {
                "stop_id": stop_id,
                "name": name.title() if name.isupper() else name,
                "lat": float(static["lat"]),
                "lng": float(static["lng"]),
            }
        )

    if len(stops) >= MIN_STOPS:
        print(f"Comuline OK ({len(stops)} Jakarta KRL stops with static coords)")
        return stops

    print(
        f"Comuline returned {len(rows)} stations but only {len(stops)} "
        f"matched static coords; using static fallback"
    )
    return None


def fetch(out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    source = "comuline"
    stops = fetch_comuline()
    if not stops:
        source = "static"
        stops = load_static()

    out_path.write_text(json.dumps(stops, indent=2), encoding="utf-8")
    meta = out_path.with_suffix(".meta.txt")
    meta.write_text(
        f"fetched_at={datetime.now(UTC).isoformat()}\nsource={source}\nstops={len(stops)}\n",
        encoding="utf-8",
    )
    print(f"Saved {len(stops)} KRL stops ({source}) -> {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/gtfs/krl_stops.json")
    args = parser.parse_args()
    fetch(Path(args.out))
