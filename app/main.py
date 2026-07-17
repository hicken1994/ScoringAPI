"""Scoring API — FastAPI application entry point."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import cache, ml
from app.auth import create_access_token, verify_api_key
from app.config import settings
from app.models import TokenRequest, TokenResponse
from app.routers import health, model, scoring

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Investment property scoring API — rule-based + ML predictions",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scoring.router)
app.include_router(model.router)
app.include_router(health.router)


@app.on_event("startup")
def startup():
    """Initialize services on boot."""
    cache.init_redis()
    ml.load_model()


@app.post("/token", response_model=TokenResponse, tags=["auth"])
def get_token(req: TokenRequest):
    """Exchange API key for JWT token."""
    user_id = verify_api_key(req.api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    token = create_access_token(user_id)
    return TokenResponse(access_token=token)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
