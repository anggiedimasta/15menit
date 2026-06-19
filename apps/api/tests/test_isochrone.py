import math

from fastapi.testclient import TestClient
from shapely.geometry import Point, shape

from app.main import app
from app.services.routing import mock_isochrone_polygon

client = TestClient(app)

MONAS = {"lat": -6.1754, "lng": 106.8272}


def test_walk_isochrone_monas() -> None:
    response = client.post("/isochrone/walk", json={**MONAS, "minutes": 15})
    assert response.status_code == 200
    data = response.json()
    assert data["geometry"]["type"] == "Polygon"
    coords = data["geometry"]["coordinates"][0]
    assert len(coords) > 3


def test_mock_isochrone_not_perfect_circle() -> None:
    geom = mock_isochrone_polygon(MONAS["lat"], MONAS["lng"], 15, "walking")
    poly = shape(geom)
    centroid = poly.centroid
    ring = geom["coordinates"][0][:-1]
    distances = [Point(c).distance(centroid) for c in ring]
    mean_d = sum(distances) / len(distances)
    variance = sum((d - mean_d) ** 2 for d in distances) / len(distances)
    cv = math.sqrt(variance) / mean_d
    assert cv > 0.03


def test_walk_isochrone_outside_bbox() -> None:
    response = client.post("/isochrone/walk", json={"lat": 0, "lng": 0, "minutes": 15})
    assert response.status_code == 400


def test_isochrone_cache_hit() -> None:
    payload = {**MONAS, "minutes": 15}
    first = client.post("/isochrone/walk", json=payload).json()
    second = client.post("/isochrone/walk", json=payload).json()
    assert first["geometry"] == second["geometry"]
    assert second["properties"]["cached"] is True


def test_transit_isochrone_larger_than_walk_mock() -> None:
    walk = client.post("/isochrone/walk", json={**MONAS, "minutes": 30}).json()
    transit = client.post("/isochrone/transit", json={**MONAS, "minutes": 30}).json()
    walk_area = shape(walk["geometry"]).area
    transit_area = shape(transit["geometry"]).area
    assert transit_area >= walk_area
    assert transit["properties"]["modes_used"] == ["WALK", "TRANSIT"]
