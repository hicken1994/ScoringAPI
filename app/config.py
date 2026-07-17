from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Scoring API"
    debug: bool = False

    # JWT
    jwt_secret: str = "changeme-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    # Rate limiting
    rate_limit_per_minute: int = 60

    # ML model
    model_path: str = "model/classifier.pkl"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
