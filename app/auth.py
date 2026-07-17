"""JWT authentication utilities."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pre-hashed API keys (in production, store in DB)
API_KEYS: dict[str, str] = {
    "demo-key-12345": "user_001",
    "admin-key-67890": "admin",
}


def verify_api_key(api_key: str) -> str | None:
    """Verify API key and return user_id."""
    return API_KEYS.get(api_key)


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Decode JWT token and return user_id, or None if invalid."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None
