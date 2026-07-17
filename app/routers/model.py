"""Model endpoints — train, predict, metrics."""

from fastapi import APIRouter, HTTPException

from app import ml
from app.models import (
    ModelMetrics,
    PredictRequest,
    PredictResponse,
    TrainRequest,
    TrainResponse,
)

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/metrics", response_model=ModelMetrics)
def model_metrics():
    """Get ML model metrics."""
    if not ml.is_loaded():
        return ModelMetrics()
    m = ml.get_metrics()
    return ModelMetrics(
        accuracy=m.get("accuracy"),
        n_samples=m.get("n_samples"),
        n_train=m.get("n_train"),
        n_test=m.get("n_test"),
        feature_importance=m.get("feature_importance"),
        classification_report=m.get("classification_report"),
        confusion_matrix=m.get("confusion_matrix"),
    )


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    """Predict investment decision using trained ML model."""
    if not ml.is_loaded():
        raise HTTPException(
            status_code=409,
            detail="Model not trained yet. POST /model/train first.",
        )
    result = ml.predict(req.model_dump())
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return PredictResponse(**result)


@router.post("/train", response_model=TrainResponse)
def train_model(req: TrainRequest):
    """Train RandomForestClassifier from property records.

    Requires at least 10 records with features + decision labels.
    Model is persisted to disk and immediately available for /predict.
    """
    records = [r.model_dump() for r in req.records]
    result = ml.train(records)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return TrainResponse(
        accuracy=result["accuracy"],
        n_samples=result["n_samples"],
        n_train=result["n_train"],
        n_test=result["n_test"],
        feature_importance=result["feature_importance"],
    )
