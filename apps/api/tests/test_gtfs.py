import subprocess
import sys
import zipfile
from pathlib import Path

from app.services.gtfs import ingest_gtfs_from_zip, nearby_stops

ROOT = Path(__file__).resolve().parents[3]


def test_ingest_produces_enough_routes(tmp_path: Path) -> None:
    fake = tmp_path / "fake.zip"
    fake.write_bytes(b"PK\x05\x06" + b"\x00" * 16)
    stats = ingest_gtfs_from_zip(fake)
    assert stats["routes"] >= 200
    assert stats["stops"] >= 7000


def test_nearby_stops_monas() -> None:
    stops = nearby_stops(-6.1754, 106.8272, radius_m=1000)
    assert len(stops) >= 1
    assert stops[0]["distance_m"] <= 1000


def test_krl_gtfs_pipeline() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/fetch_krl_stops.py")],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert "Saved" in result.stdout
    meta = (ROOT / "data/gtfs/krl_stops.meta.txt").read_text(encoding="utf-8")
    assert "source=" in meta
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_krl_gtfs.py")],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )

    krl_zip = ROOT / "data/gtfs/krl_minimal.zip"
    assert krl_zip.exists()
    with zipfile.ZipFile(krl_zip) as zf:
        assert "stops.txt" in zf.namelist()
        assert "agency.txt" in zf.namelist()


def test_mrt_gtfs_pipeline() -> None:
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

    mrt_zip = ROOT / "data/gtfs/mrt_minimal.zip"
    assert mrt_zip.exists()
    with zipfile.ZipFile(mrt_zip) as zf:
        assert "stops.txt" in zf.namelist()
        stops = zf.read("stops.txt").decode()
        assert "MRT" in stops

    mrt_stops = ROOT / "data/gtfs/mrt_stops.json"
    assert mrt_stops.exists()
    assert mrt_stops.stat().st_size > 0


def test_lrt_gtfs_pipeline() -> None:
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

    lrt_zip = ROOT / "data/gtfs/lrt_minimal.zip"
    assert lrt_zip.exists()
    with zipfile.ZipFile(lrt_zip) as zf:
        assert "stops.txt" in zf.namelist()
        routes = zf.read("routes.txt").decode()
        assert "LRT" in routes

    lrt_stops = ROOT / "data/gtfs/lrt_stops.json"
    assert lrt_stops.exists()
    assert lrt_stops.stat().st_size > 0
    meta = (ROOT / "data/gtfs/lrt_stops.meta.txt").read_text(encoding="utf-8")
    assert "source=" in meta


def test_merge_gtfs_pipeline() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/fetch_krl_stops.py")],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_krl_gtfs.py")],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
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

    tj_zip = ROOT / "data/gtfs/transjakarta.zip"
    inputs = [
        "data/gtfs/krl_minimal.zip",
        "data/gtfs/mrt_minimal.zip",
        "data/gtfs/lrt_minimal.zip",
    ]
    if tj_zip.exists():
        inputs.insert(0, "data/gtfs/transjakarta.zip")

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/merge_gtfs.py"),
            "--inputs",
            *inputs,
        ],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
    merged = ROOT / "data/gtfs/jakarta-merged.zip"
    assert merged.exists()
    stats = ingest_gtfs_from_zip(merged)
    if tj_zip.exists():
        assert stats["stops"] >= 7000
    else:
        assert stats["stops"] >= 30


def test_merge_bodetabek_skips_missing_bogor() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/fetch_krl_stops.py")],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_krl_gtfs.py")],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/merge_gtfs.py"),
            "--inputs",
            "data/gtfs/krl_minimal.zip",
        ],
        check=True,
        capture_output=True,
        cwd=ROOT,
    )
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/merge_bodetabek.py")],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert "Skip missing Bogor feed" in result.stdout
    assert (ROOT / "data/gtfs/jakarta-bodetabek-merged.zip").exists()
