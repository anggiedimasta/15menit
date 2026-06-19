import zipfile
from pathlib import Path

from app.services.transit import _gtfs_trip_duration_min, _load_merged_feed

ROOT = Path(__file__).resolve().parents[3]


def test_gtfs_stop_times_duration_when_merged_feed(monkeypatch) -> None:
    import app.services.transit as transit

    transit._load_merged_feed.cache_clear()

    import subprocess
    import sys

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/fetch_mrt_stops.py")],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_mrt_gtfs.py")],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/merge_gtfs.py"),
            "--inputs",
            "data/gtfs/mrt_minimal.zip",
        ],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )

    feed = _load_merged_feed()
    assert feed is not None

    with zipfile.ZipFile(ROOT / "data/gtfs/mrt_minimal.zip") as zf:
        stops_txt = zf.read("stops.txt").decode()
        first_id = stops_txt.splitlines()[1].split(",")[0]
        last_line = stops_txt.strip().splitlines()[-1]
        last_id = last_line.split(",")[0]

    duration = _gtfs_trip_duration_min(first_id, last_id)
    assert duration is not None
    minutes, route_id, line_name = duration
    assert minutes >= 1
    assert route_id
    assert line_name

    transit._load_merged_feed.cache_clear()


def test_lrt_line_name_from_merged_feed() -> None:
    import subprocess
    import sys

    import app.services.transit as transit

    transit._load_merged_feed.cache_clear()

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/fetch_lrt_stops.py")],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_lrt_gtfs.py")],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/merge_gtfs.py"),
            "--inputs",
            "data/gtfs/lrt_minimal.zip",
        ],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )

    feed = transit._load_merged_feed()
    assert feed is not None

    with zipfile.ZipFile(ROOT / "data/gtfs/lrt_minimal.zip") as zf:
        stops_txt = zf.read("stops.txt").decode()
        first_id = stops_txt.splitlines()[1].split(",")[0]

    line_name = transit._line_name_for_stop(feed, first_id)
    assert line_name
    assert "LRT" in line_name

    transit._load_merged_feed.cache_clear()
