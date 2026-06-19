import csv
import io
import zipfile

import pytest

from app.services.gtfs import (
    _load_stops_from_gtfs_csv,
    clear_stops_cache,
    load_stops,
    nearby_stops,
)


def _write_minimal_gtfs_zip(path, stops: list[dict[str, str]]) -> None:
    agency = "agency_id,agency_name,agency_url,agency_timezone\nTJ,TJ,https://example.com,Asia/Jakarta\n"
    routes = "route_id,agency_id,route_short_name,route_type\nR1,TJ,1,3\n"
    trips = "route_id,service_id,trip_id\nR1,WD,T1\n"
    stop_times_rows = "\n".join(
        f"T1,{stop['stop_id']},0" for stop in stops
    )
    stop_times = f"trip_id,stop_id,stop_sequence\n{stop_times_rows}\n"
    stops_csv = io.StringIO()
    writer = csv.DictWriter(
        stops_csv,
        fieldnames=["stop_id", "stop_name", "stop_lat", "stop_lon"],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(stops)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("agency.txt", agency)
        zf.writestr("routes.txt", routes)
        zf.writestr("trips.txt", trips)
        zf.writestr("stop_times.txt", stop_times)
        zf.writestr("stops.txt", stops_csv.getvalue())


def test_load_stops_from_gtfs_csv(tmp_path) -> None:
    zip_path = tmp_path / "mini.zip"
    _write_minimal_gtfs_zip(
        zip_path,
        [
            {
                "stop_id": "GTFS001",
                "stop_name": "Halte Test",
                "stop_lat": "-6.1754",
                "stop_lon": "106.8272",
            }
        ],
    )
    stops = _load_stops_from_gtfs_csv(zip_path)
    assert len(stops) == 1
    assert stops[0]["stop_id"] == "GTFS001"
    assert stops[0]["modes"] == ["bus"]


def test_load_stops_prefers_merged_gtfs_zip(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_stops_cache()
    zip_path = tmp_path / "jakarta-merged.zip"
    _write_minimal_gtfs_zip(
        zip_path,
        [
            {
                "stop_id": "MERGED99",
                "stop_name": "Merged Stop",
                "stop_lat": "-6.1754",
                "stop_lon": "106.8272",
            }
        ],
    )
    monkeypatch.setattr(
        "app.services.gtfs._merged_gtfs_path",
        lambda: zip_path,
    )

    stops = load_stops()
    assert any(s["stop_id"] == "MERGED99" for s in stops)
    clear_stops_cache()


def test_nearby_stops_uses_gtfs_data(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_stops_cache()
    zip_path = tmp_path / "jakarta-merged.zip"
    _write_minimal_gtfs_zip(
        zip_path,
        [
            {
                "stop_id": "NEAR001",
                "stop_name": "Near Monas",
                "stop_lat": "-6.1754",
                "stop_lon": "106.8272",
            },
            {
                "stop_id": "FAR999",
                "stop_name": "Far Away",
                "stop_lat": "-6.5",
                "stop_lon": "107.0",
            },
        ],
    )
    monkeypatch.setattr(
        "app.services.gtfs._merged_gtfs_path",
        lambda: zip_path,
    )

    results = nearby_stops(-6.1754, 106.8272, radius_m=500)
    stop_ids = {s["stop_id"] for s in results}
    assert "NEAR001" in stop_ids
    assert "FAR999" not in stop_ids
    clear_stops_cache()
