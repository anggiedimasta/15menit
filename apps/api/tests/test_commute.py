from fastapi.testclient import TestClient

from app.main import app
from app.services.transit import estimate_transit_fare

client = TestClient(app)

ORIGIN = {"lat": -6.1754, "lng": 106.8272}
DEST = {"lat": -6.2088, "lng": 106.8456}

FIXTURE_PAIRS = [
    ({"lat": -6.1754, "lng": 106.8272}, {"lat": -6.2088, "lng": 106.8456}),
    ({"lat": -6.1944, "lng": 106.8227}, {"lat": -6.2045, "lng": 106.8245}),
    ({"lat": -6.2, "lng": 106.82}, {"lat": -6.21, "lng": 106.85}),
    ({"lat": -6.18, "lng": 106.83}, {"lat": -6.19, "lng": 106.84}),
    ({"lat": -6.17, "lng": 106.82}, {"lat": -6.21, "lng": 106.84}),
]


def test_commute_compare_fastest_mode() -> None:
    response = client.post(
        "/commute/compare",
        json={"origin": ORIGIN, "destination": DEST},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fastest_mode"] in ("walking", "transit", "car", "motorcycle")
    modes = [r["mode"] for r in data["results"]]
    assert "transit" in modes
    fastest = next(r for r in data["results"] if r["is_fastest"])
    assert fastest["mode"] == data["fastest_mode"]


def test_commute_transit_legs() -> None:
    response = client.post(
        "/commute/compare",
        json={"origin": ORIGIN, "destination": DEST},
    )
    transit = next(r for r in response.json()["results"] if r["mode"] == "transit")
    assert len(transit["legs"]) >= 3
    assert any(leg.get("route_id") for leg in transit["legs"])
    assert any(leg.get("line_name") for leg in transit["legs"])
    assert transit.get("route_polyline")
    assert len(transit["route_polyline"]) >= 2


def test_commute_fixture_pairs_rank_consistently() -> None:
    for origin, dest in FIXTURE_PAIRS:
        response = client.post(
            "/commute/compare",
            json={"origin": origin, "destination": dest},
        )
        assert response.status_code == 200
        data = response.json()
        durations = [r["duration_min"] for r in data["results"]]
        assert durations == sorted(durations)
        fastest = next(r for r in data["results"] if r["is_fastest"])
        assert fastest["mode"] == data["fastest_mode"]


def test_tj_only_fare() -> None:
    cost, breakdown = estimate_transit_fare([{"agency": "TJ"}])
    assert cost == 3500
    assert breakdown[0]["agency"] == "TransJakarta"


def test_krl_fare() -> None:
    cost, _ = estimate_transit_fare(
        [{"agency": "KRL", "station_pair": "Manggarai-Sudirman"}]
    )
    assert cost == 5000
