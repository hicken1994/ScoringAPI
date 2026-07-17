import pytest
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


# ── ML endpoints ──


def _generate_training_data(n: int = 50) -> list[dict]:
    """Generate synthetic training data for tests."""
    import random

    records = []
    for _ in range(n):
        descuento = random.uniform(0, 40)
        precio = random.uniform(0, 25)
        liquidez = random.choice([5, 10, 15])
        tamano = random.choice([5, 10])
        precio_total = random.uniform(100000, 500000)
        metros = random.uniform(40, 150)
        precio_m2 = precio_total / metros
        rent = random.uniform(-10, 30)

        # Synthesize decision from score
        score = descuento * 1.2 + precio * 1.2 + liquidez + tamano
        if score > 55 and rent > 5:
            decision = "COMPRAR"
        elif score > 35:
            decision = "NEGOCIAR"
        else:
            decision = "DESCARTAR"

        records.append({
            "score_descuento": descuento,
            "score_precio": precio,
            "score_liquidez": liquidez,
            "score_tamano": tamano,
            "precio_total": precio_total,
            "metros": metros,
            "precio_m2": round(precio_m2, 2),
            "rentabilidad_estimada": rent,
            "decision": decision,
        })
    return records


def test_train_model():
    data = _generate_training_data(50)
    resp = client.post("/model/train", json={"records": data})
    assert resp.status_code == 200
    result = resp.json()
    assert result["accuracy"] > 0
    assert result["n_samples"] == 50
    assert len(result["feature_importance"]) == 8


def test_train_insufficient_data():
    data = _generate_training_data(5)
    resp = client.post("/model/train", json={"records": data})
    assert resp.status_code == 422


def test_train_missing_decision():
    data = _generate_training_data(20)
    for r in data:
        del r["decision"]
    resp = client.post("/model/train", json={"records": data})
    assert resp.status_code == 422


def test_predict_after_train():
    # Train first
    data = _generate_training_data(50)
    client.post("/model/train", json={"records": data})

    # Predict
    resp = client.post("/model/predict", json={
        "score_descuento": 30,
        "score_precio": 20,
        "score_liquidez": 15,
        "score_tamano": 10,
        "precio_total": 180000,
        "metros": 75,
        "precio_m2": 2400,
        "rentabilidad_estimada": 25,
    })
    assert resp.status_code == 200
    result = resp.json()
    assert result["prediction"] in ("COMPRAR", "NEGOCIAR", "DESCARTAR")
    assert 0 <= result["confidence"] <= 1
    assert sum(result["probabilities"].values()) == pytest.approx(1.0)


def test_predict_before_train():
    """Predict should fail if no model is loaded."""
    from app import ml
    ml._model = None  # Force unload

    resp = client.post("/model/predict", json={
        "score_descuento": 30,
        "score_precio": 20,
        "score_liquidez": 15,
        "score_tamano": 10,
        "precio_total": 180000,
        "metros": 75,
        "precio_m2": 2400,
        "rentabilidad_estimada": 25,
    })
    assert resp.status_code == 409
