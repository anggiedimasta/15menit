#!/usr/bin/env python3
"""Build minimal KRL GTFS zip from stop list (community supplement)."""

from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from pathlib import Path

DEFAULT_STOPS = Path("data/gtfs/krl_stops.json")
STATIC_STOPS = Path("data/gtfs/static/krl_stops.json")


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
            "agency_id": "KRL",
            "agency_name": "KRL Commuter Line",
            "agency_url": "https://www.krl.co.id",
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
            "route_id": "KRL-LOOP",
            "agency_id": "KRL",
            "route_short_name": "KRL",
            "route_long_name": "Jakarta Commuter Line",
            "route_type": "2",
        }
    ]
    calendar = [
        {
            "service_id": "KRL-WEEKDAY",
            "monday": "1",
            "tuesday": "1",
            "wednesday": "1",
            "thursday": "1",
            "friday": "1",
            "saturday": "0",
            "sunday": "0",
            "start_date": "20260101",
            "end_date": "20261231",
        }
    ]
    trips = [
        {
            "route_id": "KRL-LOOP",
            "service_id": "KRL-WEEKDAY",
            "trip_id": "KRL-TRIP-1",
            "trip_headsign": "Loop",
        }
    ]
    stop_times = [
        {
            "trip_id": "KRL-TRIP-1",
            "arrival_time": f"07:{30 + i * 2:02d}:00",
            "departure_time": f"07:{30 + i * 2:02d}:00",
            "stop_id": s["stop_id"],
            "stop_sequence": str(i + 1),
        }
        for i, s in enumerate(stops)
    ]

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
    print(f"Built KRL GTFS ({len(stops)} stops) -> {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stops", default=str(DEFAULT_STOPS))
    parser.add_argument("--output", default="data/gtfs/krl_minimal.zip")
    args = parser.parse_args()
    build(Path(args.stops), Path(args.output))
