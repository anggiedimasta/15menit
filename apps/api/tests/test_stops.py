from fastapi.testclient import TestClient

from app.main import app
from app.services.commute import union_polygons
from app.services.routing import mock_isochrone_polygon

client = TestClient(app)


def test_nearby_stops_endpoint() -> None:
    response = client.post(
        "/stops/nearby",
        json={"lat": -6.1754, "lng": 106.8272, "radius_m": 1000},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_union_area_gte_single() -> None:
    a = mock_isochrone_polygon(-6.1754, 106.8272, 15, "walking")
    b = mock_isochrone_polygon(-6.1944, 106.8227, 15, "walking")
    from shapely.geometry import shape

    union = union_polygons([a, b])
    assert shape(union).area >= shape(a).area


def test_coverage_pct_range() -> None:
    response = client.post(
        "/coverage/kecamatan",
        json={"kecamatan_id": "menteng"},
    )
    data = response.json()
    assert 0 <= data["coverage_pct"] <= 100
    assert data["sample_count"] == 500
