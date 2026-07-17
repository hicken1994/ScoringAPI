"""Scoring endpoints."""

import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import decode_access_token
from app.cache import get_cached, set_cached
from app.models import BatchRequest, BatchResponse, PropertyInput, ScoreResult
from app.rate_limit import get_remaining, is_rate_limited
from app.scoring import compute_score

router = APIRouter(prefix="/score", tags=["scoring"])


def require_auth(request: Request) -> str:
    """Extract and validate JWT from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = auth.removeprefix("Bearer ")
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


def check_rate_limit(request: Request) -> None:
    """Check rate limit using API key from header."""
    api_key = request.headers.get("X-API-Key", "anonymous")
    if is_rate_limited(api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    remaining = get_remaining(api_key)
    request.state.rate_remaining = remaining


@router.post("", response_model=ScoreResult)
def score_property(
    prop: PropertyInput,
    request: Request,
    user_id: str = Depends(require_auth),
):
    """Score a single property."""
    check_rate_limit(request)

    # Check cache
    cache_key = f"score:{hashlib.md5(json.dumps(prop.model_dump(), sort_keys=True).encode()).hexdigest()}"
    cached = get_cached(cache_key)
    if cached:
        return ScoreResult(**cached)

    result = compute_score(
        precio_total=prop.precio_total,
        metros=prop.metros,
        precio_m2=prop.precio_m2,
        precio_m2_barrio=prop.precio_m2_barrio,
    )

    set_cached(cache_key, result)
    return ScoreResult(**result)


@router.post("/batch", response_model=BatchResponse)
def score_batch(
    batch: BatchRequest,
    request: Request,
    user_id: str = Depends(require_auth),
):
    """Score multiple properties in one request."""
    check_rate_limit(request)

    results = []
    cached_count = 0

    for prop in batch.properties:
        cache_key = f"score:{hashlib.md5(json.dumps(prop.model_dump(), sort_keys=True).encode()).hexdigest()}"
        cached = get_cached(cache_key)

        if cached:
            results.append(ScoreResult(**cached))
            cached_count += 1
        else:
            result = compute_score(
                precio_total=prop.precio_total,
                metros=prop.metros,
                precio_m2=prop.precio_m2,
                precio_m2_barrio=prop.precio_m2_barrio,
            )
            set_cached(cache_key, result)
            results.append(ScoreResult(**result))

    return BatchResponse(results=results, total=len(results), cached=cached_count)
