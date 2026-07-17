"""Health check endpoint."""

from fastapi import APIRouter

from app import cache, ml
from app.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    """Health check with model and Redis status."""
    return HealthResponse(
        status="ok",
        model_loaded=ml.is_loaded(),
        redis_connected=cache.is_available(),
    )
