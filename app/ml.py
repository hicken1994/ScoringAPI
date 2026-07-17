"""ML model — train, load, predict. Scikit-learn lazy-loaded."""

import json
import logging
import os
import pickle

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "classifier.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

FEATURE_COLS = [
    "score_descuento", "score_precio", "score_liquidez", "score_tamano",
    "precio_total", "metros", "precio_m2", "rentabilidad_estimada",
]

LABEL_MAP = {0: "DESCARTAR", 1: "NEGOCIAR", 2: "COMPRAR"}
REVERSE_MAP = {"COMPRAR": 2, "NEGOCIAR": 1, "DESCARTAR": 0}

_model = None
_metrics: dict = {}


def is_loaded() -> bool:
    return _model is not None


def get_metrics() -> dict:
    return _metrics


def load_model(model_path: str | None = None) -> bool:
    """Load trained model from disk. Returns True if loaded."""
    global _model, _metrics

    path = model_path or MODEL_PATH
    metrics_path = path.replace("classifier.pkl", "metrics.json")

    if not os.path.exists(path):
        logger.warning("Model not found at %s", path)
        return False

    try:
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


def train(records: list[dict]) -> dict:
    """Train RandomForestClassifier from property records.

    Each record must have FEATURE_COLS + 'decision' (COMPRAR/NEGOCIAR/DESCARTAR).
    Returns metrics dict. Model is stored in module-level _model.
    """
    global _model, _metrics

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    from sklearn.model_selection import train_test_split

    df = pd.DataFrame(records)

    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        return {"error": f"Missing columns: {missing}"}

    if "decision" not in df.columns:
        return {"error": "Missing 'decision' column (COMPRAR/NEGOCIAR/DESCARTAR)"}

    X = df[FEATURE_COLS].copy()
    y = df["decision"].map(REVERSE_MAP)

    valid = y.notna()
    X = X[valid].fillna(0)
    y = y[valid].astype(int)

    present_labels = sorted(y.unique())
    if len(present_labels) < 2:
        return {"error": f"Need at least 2 classes, got {len(present_labels)}"}

    stratify = y if y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify,
    )

    clf = RandomForestClassifier(
        n_estimators=100, max_depth=12, random_state=42, n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    report = classification_report(
        y_test, y_pred,
        labels=[0, 1, 2],
        target_names=["DESCARTAR", "NEGOCIAR", "COMPRAR"],
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])

    feature_importance = [
        {"feature": col, "importance": round(float(v), 4)}
        for col, v in sorted(
            zip(FEATURE_COLS, clf.feature_importances_), key=lambda x: -x[1]
        )
    ]

    _metrics = {
        "accuracy": round(float(acc), 4),
        "n_samples": int(len(df)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "feature_importance": feature_importance,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
    }
    _model = clf

    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    with open(METRICS_PATH, "w") as f:
        json.dump(_metrics, f, indent=2)

    logger.info("Model trained: accuracy=%.4f, samples=%d", acc, len(df))
    return _metrics


def predict(features: dict) -> dict:
    """Run prediction on loaded model.

    Args:
        dict with FEATURE_COLS keys.
    Returns:
        dict with prediction, confidence, probabilities.
    """
    global _model

    if _model is None:
        return {"error": "Model not loaded. Call /train first."}

    X = np.array([[features.get(col, 0) for col in FEATURE_COLS]])
    prediction = _model.predict(X)[0]
    proba = _model.predict_proba(X)[0].tolist()

    return {
        "prediction": LABEL_MAP.get(int(prediction), "UNKNOWN"),
        "confidence": round(max(proba), 4),
        "probabilities": {
            LABEL_MAP[i]: round(p, 4) for i, p in enumerate(proba)
        },
    }
