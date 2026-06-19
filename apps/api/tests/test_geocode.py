from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_geocode_monas() -> None:
    response = client.get("/geocode/search", params={"q": "Monas"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Jakarta" in data[0]["display_name"]
    assert abs(data[0]["lat"] - (-6.1754)) < 0.1
