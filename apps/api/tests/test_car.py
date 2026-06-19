from shapely.geometry import shape
from fastapi.testclient import TestClient

from app.main import app
from app.services.routing import mock_isochrone_polygon

client = TestClient(app)

MONAS = {"lat": -6.1754, "lng": 106.8272}


def test_car_isochrone_larger_than_walk() -> None:
    walk = mock_isochrone_polygon(MONAS["lat"], MONAS["lng"], 15, "walking")
    car = mock_isochrone_polygon(MONAS["lat"], MONAS["lng"], 15, "car")
    assert shape(car).area > shape(walk).area
    walk_resp = client.post("/isochrone/walk", json={**MONAS, "minutes": 15})
    car_resp = client.post("/isochrone/car", json={**MONAS, "minutes": 15})
    assert walk_resp.status_code == 200
    assert car_resp.status_code == 200


def test_motor_faster_than_car() -> None:
    response = client.post(
        "/commute/compare",
        json={
            "origin": MONAS,
            "destination": {"lat": -6.2088, "lng": 106.8456},
        },
    )
    results = {r["mode"]: r for r in response.json()["results"]}
    assert results["motorcycle"]["duration_min"] <= results["car"]["duration_min"]
