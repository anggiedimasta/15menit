from pathlib import Path

import pytest

from app.services.gtfs import clear_stops_cache

_NO_MERGED_GTFS = Path(__file__).resolve().parent / "_no_merged_gtfs.zip"


@pytest.fixture(autouse=True)
def mock_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROUTING_MODE", "mock")
    monkeypatch.setenv("TRANSIT_MODE", "mock")
    monkeypatch.delenv("GTFS_MERGED_PATH", raising=False)
    monkeypatch.setattr(
        "app.services.gtfs._merged_gtfs_path",
        lambda: _NO_MERGED_GTFS,
    )
    clear_stops_cache()
    yield
    clear_stops_cache()
