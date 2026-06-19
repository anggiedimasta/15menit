#!/usr/bin/env python3
"""Merge Jakarta GTFS feeds (TJ + optional KRL/MRT community sources)."""

from __future__ import annotations

import argparse
import csv
import io
import math
import shutil
import zipfile
from pathlib import Path

README = """# Jakarta merged GTFS

Feeds merged by `scripts/merge_gtfs.py`.

| Agency | Source | Quality |
|--------|--------|---------|
| TransJakarta | gtfs.transjakarta.co.id | official |
| KRL | Comuline API / static fallback | community |
| MRT | GIS DPMPTSP ArcGIS / static fallback | community |
| LRT | GIS DPMPTSP ArcGIS / static fallback | community |

## Quick start

```powershell
python scripts/download_gtfs.py
python scripts/fetch_krl_stops.py
python scripts/build_krl_gtfs.py
python scripts/fetch_mrt_stops.py
python scripts/build_mrt_gtfs.py
python scripts/fetch_lrt_stops.py
python scripts/build_lrt_gtfs.py
python scripts/merge_gtfs.py
```

TJ-only fallback ships when KRL/MRT sources unavailable.
"""

GTFS_TABLES = (
    "agency.txt",
    "stops.txt",
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
    "calendar.txt",
    "shapes.txt",
)


def _read_csv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    if name not in zf.namelist():
        return []
    text = zf.read(name).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _write_csv(rows: list[dict[str, str]]) -> bytes:
    if not rows:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _dedup_stops(rows: list[dict[str, str]], threshold_m: float = 50) -> list[dict[str, str]]:
    kept: list[dict[str, str]] = []
    for row in rows:
        lat = float(row["stop_lat"])
        lng = float(row["stop_lon"])
        duplicate = False
        for existing in kept:
            if (
                _haversine_m(
                    lat,
                    lng,
                    float(existing["stop_lat"]),
                    float(existing["stop_lon"]),
                )
                <= threshold_m
            ):
                duplicate = True
                break
        if not duplicate:
            kept.append(row)
    return kept


def _prefix_rows(
    rows: list[dict[str, str]], prefix: str, id_fields: tuple[str, ...]
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        copy = dict(row)
        for field in id_fields:
            if field in copy and copy[field]:
                copy[field] = f"{prefix}_{copy[field]}"
        out.append(copy)
    return out


def merge_csv_feeds(inputs: list[Path], output: Path) -> None:
    merged: dict[str, list[dict[str, str]]] = {t: [] for t in GTFS_TABLES}
    for idx, path in enumerate(inputs):
        prefix = path.stem.upper().replace("-", "_")
        with zipfile.ZipFile(path) as zf:
            agencies = _read_csv(zf, "agency.txt")
            merged["agency.txt"].extend(
                _prefix_rows(agencies, prefix, ("agency_id",))
            )
            merged["stops.txt"].extend(
                _prefix_rows(
                    _read_csv(zf, "stops.txt"),
                    prefix,
                    ("stop_id", "parent_station", "zone_id"),
                )
            )
            merged["routes.txt"].extend(
                _prefix_rows(
                    _read_csv(zf, "routes.txt"),
                    prefix,
                    ("route_id", "agency_id"),
                )
            )
            merged["trips.txt"].extend(
                _prefix_rows(
                    _read_csv(zf, "trips.txt"),
                    prefix,
                    ("route_id", "service_id", "trip_id", "shape_id"),
                )
            )
            merged["stop_times.txt"].extend(
                _prefix_rows(
                    _read_csv(zf, "stop_times.txt"),
                    prefix,
                    ("trip_id", "stop_id"),
                )
            )
            merged["calendar.txt"].extend(
                _prefix_rows(
                    _read_csv(zf, "calendar.txt"),
                    prefix,
                    ("service_id",),
                )
            )
            shapes = _read_csv(zf, "shapes.txt")
            if shapes:
                merged["shapes.txt"].extend(
                    _prefix_rows(shapes, prefix, ("shape_id",))
                )

    merged["stops.txt"] = _dedup_stops(merged["stops.txt"])

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as out_zip:
        for table, rows in merged.items():
            if rows:
                out_zip.writestr(table, _write_csv(rows))
    print(f"Merged {len(inputs)} feeds (CSV concat + 50m dedup) -> {output}")


def validate_zip(path: Path) -> dict[str, int]:
    try:
        import gtfs_kit as gk

        feed = gk.read_feed(str(path), dist_units="m")
        return {
            "routes": len(feed.routes),
            "stops": len(feed.stops),
            "trips": len(feed.trips),
            "feed_version": "gtfs-kit",
        }
    except ImportError:
        with zipfile.ZipFile(path) as zf:
            stops = len(_read_csv(zf, "stops.txt"))
            routes = len(_read_csv(zf, "routes.txt"))
        return {"routes": routes, "stops": stops, "trips": 0, "feed_version": "zip-only"}


def merge(inputs: list[Path], output: Path) -> None:
    existing = [p for p in inputs if p.exists()]
    if not existing:
        raise FileNotFoundError(f"No GTFS inputs found: {inputs}")

    output.parent.mkdir(parents=True, exist_ok=True)
    if len(existing) == 1:
        shutil.copy(existing[0], output)
        print(f"Copied single feed -> {output}")
    else:
        merge_csv_feeds(existing, output)

    stats = validate_zip(output)
    print(f"Validated: {stats['routes']} routes, {stats['stops']} stops")
    readme = output.parent / "README.md"
    readme.write_text(README, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "data/gtfs/transjakarta.zip",
            "data/gtfs/krl_minimal.zip",
            "data/gtfs/mrt_minimal.zip",
            "data/gtfs/lrt_minimal.zip",
        ],
    )
    parser.add_argument("--output", default="data/gtfs/jakarta-merged.zip")
    args = parser.parse_args()
    merge([Path(p) for p in args.inputs], Path(args.output))
