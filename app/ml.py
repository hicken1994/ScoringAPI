"""ML model loader — lazy-loads scikit-learn to keep boot fast."""

import logging
import os
import pickle

logger = logging.getLogger(__name__)

_model = None
_metrics: dict = {}


def load_model(model_path: str | None = None) -> bool:
    """Load trained model from disk. Returns True if loaded."""
    global _model, _metrics

    path = model_path or os.getenv("MODEL_PATH", "model/classifier.pkl")
    metrics_path = path.replace("classifier.pkl", "metrics.json")

    if not os.path.exists(path):
        logger.warning("Model not found at %s", path)
        return False

    try:
        import json

        with open(path, "rb") as f:
            _model = pickle.load(f)

        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                _metrics = json.load(f)

        logger.info("Model loaded from %s", path)
        return True
    except Exception as e:
        logger.error("Failed to load model: %s", e)
        return False


def predict(features: list[float]) -> dict:
    """Run prediction on loaded model."""
    global _model

    if _model is None:
        return {"error": "Model not loaded"}

    import numpy as np

    X = np.array([features])
    prediction = _model.predict(X)[0]
    proba = _model.predict_proba(X)[0].tolist()

    label_map = {0: "DESCARTAR", 1: "NEGOCIAR", 2: "COMPRAR"}
    return {
        "prediction": label_map.get(int(prediction), "UNKNOWN"),
        "confidence": round(max(proba), 4),
        "probabilities": {
            label_map[i]: round(p, 4) for i, p in enumerate(proba)
        },
    }


def is_loaded() -> bool:
    return _model is not None


def get_metrics() -> dict:
    return _metrics
