"""Valhalla routing client tests with mocked HTTP."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.routing import (
    get_isochrone,
    get_route,
    valhalla_isochrone,
    valhalla_route,
)

MONAS = {"lat": -6.1754, "lng": 106.8272}
ISOCHRONE_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [106.82, -6.17],
                        [106.83, -6.17],
                        [106.83, -6.18],
                        [106.82, -6.18],
                        [106.82, -6.17],
                    ]
                ],
            },
        }
    ],
}

ROUTE_RESPONSE = {
    "trip": {
        "summary": {"time": 900, "length": 2.5},
        "legs": [{"shape": "m~oia@?oia@"}],
    }
}


@pytest.mark.asyncio
async def test_valhalla_isochrone_parses_feature_collection() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = ISOCHRONE_RESPONSE

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("app.services.routing.httpx.AsyncClient", return_value=mock_client):
        geometry = await valhalla_isochrone(MONAS["lat"], MONAS["lng"], 15, "pedestrian")

    assert geometry["type"] == "Polygon"
    mock_client.post.assert_awaited_once()
    call_args = mock_client.post.await_args
    assert call_args is not None
    assert call_args.args[0].endswith("/isochrone")
    assert call_args.kwargs["json"]["costing"] == "pedestrian"


@pytest.mark.asyncio
async def test_valhalla_route_parses_summary() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = ROUTE_RESPONSE

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("app.services.routing.httpx.AsyncClient", return_value=mock_client), patch(
        "app.services.routing._decode_polyline",
        return_value=[[106.8, -6.2], [106.81, -6.21]],
    ):
        duration_min, distance_m, polyline = await valhalla_route(
            -6.2, 106.8, -6.21, 106.81, "auto"
        )

    assert duration_min == 15
    assert distance_m == 2500
    assert len(polyline) >= 2


@pytest.mark.asyncio
async def test_get_isochrone_uses_valhalla_when_routing_mode_valhalla(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ROUTING_MODE", "valhalla")
    from app.config import Settings

    monkeypatch.setattr(
        "app.services.routing.settings",
        Settings.from_env(),
    )

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = ISOCHRONE_RESPONSE

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("app.services.routing.httpx.AsyncClient", return_value=mock_client):
        geometry = await get_isochrone(MONAS["lat"], MONAS["lng"], 15, "walking")

    assert geometry["type"] == "Polygon"
    assert mock_client.post.await_count == 1


@pytest.mark.asyncio
async def test_get_isochrone_falls_back_to_mock_on_valhalla_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ROUTING_MODE", "valhalla")
    from app.config import Settings

    monkeypatch.setattr(
        "app.services.routing.settings",
        Settings.from_env(),
    )

    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.ConnectError("connection refused")
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("app.services.routing.httpx.AsyncClient", return_value=mock_client):
        geometry = await get_isochrone(MONAS["lat"], MONAS["lng"], 15, "walking")

    assert geometry["type"] == "Polygon"
    assert len(geometry["coordinates"][0]) > 3


@pytest.mark.asyncio
async def test_get_route_uses_valhalla_when_routing_mode_valhalla(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ROUTING_MODE", "valhalla")
    from app.config import Settings

    monkeypatch.setattr(
        "app.services.routing.settings",
        Settings.from_env(),
    )

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = ROUTE_RESPONSE

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("app.services.routing.httpx.AsyncClient", return_value=mock_client), patch(
        "app.services.routing._decode_polyline",
        return_value=[[106.8, -6.2], [106.81, -6.21]],
    ):
        duration_min, distance_m, _polyline = await get_route(
            -6.2, 106.8, -6.21, 106.81, "car"
        )

    assert duration_min == 15
    assert distance_m == 2500
