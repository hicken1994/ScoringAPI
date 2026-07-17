from fastapi.testclient import TestClient

from app import ml
from app.main import app

client = TestClient(app)


def get_auth_headers():
    """Get JWT token for tests."""
    resp = client.post("/token", json={"api_key": "demo-key-12345"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data
    assert "redis_connected" in data


def test_token_valid():
    resp = client.post("/token", json={"api_key": "demo-key-12345"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_token_invalid():
    resp = client.post("/token", json={"api_key": "wrong-key"})
    assert resp.status_code == 401


def test_score_unauthorized():
    resp = client.post("/score", json={
        "precio_total": 200000,
        "metros": 80,
        "precio_m2": 2500,
        "precio_m2_barrio": 3000,
        "barrio": "salamanca",
    })
    assert resp.status_code == 401


def test_score_single():
    headers = get_auth_headers()
    resp = client.post("/score", json={
        "precio_total": 180000,
        "metros": 75,
        "precio_m2": 2400,
        "precio_m2_barrio": 3000,
        "barrio": "carabanchel",
        "rooms": 2,
        "bathrooms": 1,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "score_total" in data
    assert "decision" in data
    assert data["decision"] in ("COMPRAR", "NEGOCIAR", "DESCARTAR")
    assert 0 <= data["score_total"] <= 100


def test_score_batch():
    headers = get_auth_headers()
    resp = client.post("/score/batch", json={
        "properties": [
            {
                "precio_total": 180000,
                "metros": 75,
                "precio_m2": 2400,
                "precio_m2_barrio": 3000,
                "barrio": "carabanchel",
            },
            {
                "precio_total": 350000,
                "metros": 120,
                "precio_m2": 2916,
                "precio_m2_barrio": 2800,
                "barrio": "salamanca",
            },
        ]
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2


def test_model_metrics():
    resp = client.get("/model/metrics")
    assert resp.status_code == 200


def test_rate_limit():
    headers = get_auth_headers()
    for _ in range(5):
        resp = client.post("/score", json={
            "precio_total": 200000,
            "metros": 80,
            "precio_m2": 2500,
            "precio_m2_barrio": 3000,
            "barrio": "retiro",
        }, headers=headers)
        assert resp.status_code == 200
