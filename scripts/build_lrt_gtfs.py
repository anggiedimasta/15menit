#!/usr/bin/env python3
"""Build minimal LRT Jakarta + LRT Jabodebek GTFS zip from stop list."""

from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from pathlib import Path

DEFAULT_STOPS = Path("data/gtfs/lrt_stops.json")
STATIC_STOPS = Path("data/gtfs/static/lrt_stops.json")

ROUTE_META = {
    "LRT-JKT": {
        "route_id": "LRT-JKT",
        "route_short_name": "LRT",
        "route_long_name": "LRT Jakarta",
    },
    "LRT-JBD": {
        "route_id": "LRT-JBD",
        "route_short_name": "LRT-JBD",
        "route_long_name": "LRT Jabodebek",
    },
}


def _write_csv(rows: list[dict[str, str]], fieldnames: list[str]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def build(stops_path: Path, output: Path) -> None:
    if not stops_path.exists():
        stops_path = STATIC_STOPS
    stops = json.loads(stops_path.read_text(encoding="utf-8"))

    agency = [
        {
            "agency_id": "LRT",
            "agency_name": "LRT Jakarta & Jabodebek",
            "agency_url": "https://www.lrtjakarta.co.id",
            "agency_timezone": "Asia/Jakarta",
        }
    ]
    stop_rows = [
        {
            "stop_id": s["stop_id"],
            "stop_name": s["name"],
            "stop_lat": f"{s['lat']:.6f}",
            "stop_lon": f"{s['lng']:.6f}",
        }
        for s in stops
    ]
    route_rows = [
        {
            "route_id": meta["route_id"],
            "agency_id": "LRT",
            "route_short_name": meta["route_short_name"],
            "route_long_name": meta["route_long_name"],
            "route_type": "0",
        }
        for meta in ROUTE_META.values()
    ]
    calendar = [
        {
            "service_id": "LRT-WEEKDAY",
            "monday": "1",
            "tuesday": "1",
            "wednesday": "1",
            "thursday": "1",
            "friday": "1",
            "saturday": "1",
            "sunday": "1",
            "start_date": "20260101",
            "end_date": "20261231",
        }
    ]
    trips: list[dict[str, str]] = []
    stop_times: list[dict[str, str]] = []
    for line_id, meta in ROUTE_META.items():
        line_stops = [s for s in stops if s.get("line", "LRT-JKT") == line_id]
        if not line_stops:
            continue
        trip_id = f"{line_id}-TRIP-1"
        trips.append(
            {
                "route_id": meta["route_id"],
                "service_id": "LRT-WEEKDAY",
                "trip_id": trip_id,
                "trip_headsign": line_stops[-1]["name"],
            }
        )
        for i, stop in enumerate(line_stops):
            stop_times.append(
                {
                    "trip_id": trip_id,
                    "arrival_time": f"07:{30 + i * 3:02d}:00",
                    "departure_time": f"07:{30 + i * 3:02d}:00",
                    "stop_id": stop["stop_id"],
                    "stop_sequence": str(i + 1),
                }
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("agency.txt", _write_csv(agency, list(agency[0].keys())))
        zf.writestr("stops.txt", _write_csv(stop_rows, list(stop_rows[0].keys())))
        zf.writestr("routes.txt", _write_csv(route_rows, list(route_rows[0].keys())))
        zf.writestr("calendar.txt", _write_csv(calendar, list(calendar[0].keys())))
        zf.writestr("trips.txt", _write_csv(trips, list(trips[0].keys())))
        zf.writestr(
            "stop_times.txt", _write_csv(stop_times, list(stop_times[0].keys()))
        )
    print(f"Built LRT GTFS ({len(stops)} stops, {len(trips)} trips) -> {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stops", default=str(DEFAULT_STOPS))
    parser.add_argument("--output", default="data/gtfs/lrt_minimal.zip")
    args = parser.parse_args()
    build(Path(args.stops), Path(args.output))
