"""Model metrics endpoint."""

from fastapi import APIRouter

from app.ml import get_metrics, is_loaded
from app.models import ModelMetrics

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/metrics", response_model=ModelMetrics)
def model_metrics():
    """Get ML model metrics."""
    if not is_loaded():
        return ModelMetrics()
    metrics = get_metrics()
    return ModelMetrics(
        accuracy=metrics.get("accuracy"),
        n_samples=metrics.get("n_samples"),
        feature_importance=metrics.get("feature_importance"),
    )
