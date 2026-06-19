import pytest

from app.config import Settings, _resolve_routing_mode


def test_resolve_routing_mode_respects_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROUTING_MODE", "mock")
    assert _resolve_routing_mode("http://localhost:8002", True) == "mock"


def test_resolve_routing_mode_auto_uses_valhalla_when_reachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ROUTING_MODE", "auto")
    assert _resolve_routing_mode("http://localhost:8002", True) == "valhalla"
    assert _resolve_routing_mode("http://localhost:8002", False) == "mock"


def test_resolve_routing_mode_forces_valhalla(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ROUTING_MODE", "valhalla")
    assert _resolve_routing_mode("http://127.0.0.1:1", False) == "valhalla"


def test_settings_from_env_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROUTING_MODE", "mock")
    monkeypatch.setenv("TRANSIT_MODE", "mock")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings.from_env()
    assert settings.routing_mode == "mock"
    assert settings.database_url is None
