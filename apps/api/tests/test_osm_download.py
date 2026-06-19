import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_osm_download_script_exists() -> None:
    sh = ROOT / "scripts" / "download-osm.sh"
    ps1 = ROOT / "scripts" / "download-osm.ps1"
    assert sh.exists()
    assert ps1.exists()


def test_osm_file_mock_for_ci(tmp_path: Path, monkeypatch) -> None:
    osm_dir = tmp_path / "osm"
    osm_dir.mkdir()
    fake = osm_dir / "java-latest.osm.pbf"
    fake.write_bytes(b"x" * (101 * 1024 * 1024))
    assert fake.stat().st_size > 100 * 1024 * 1024
