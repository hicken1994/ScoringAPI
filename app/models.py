from pydantic import BaseModel, Field


class PropertyInput(BaseModel):
    precio_total: float = Field(..., gt=0, description="Total price in EUR")
    metros: float = Field(..., gt=0, description="Surface area in m²")
    precio_m2: float = Field(..., gt=0, description="Price per m²")
    precio_m2_barrio: float = Field(..., gt=0, description="Avg price per m² in district")
    rooms: int = Field(default=0, ge=0)
    bathrooms: int = Field(default=0, ge=0)
    has_lift: int = Field(default=0, ge=0, le=1)
    has_terrace: int = Field(default=0, ge=0, le=1)
    barrio: str = Field(..., min_length=1, description="District name")
    latitude: float | None = None
    longitude: float | None = None


class ScoreResult(BaseModel):
    score_total: float
    score_descuento: float
    score_precio: float
    score_liquidez: float
    score_tamano: float
    decision: str
    rentabilidad_estimada: float


class BatchRequest(BaseModel):
    properties: list[PropertyInput] = Field(..., max_length=1000)


class BatchResponse(BaseModel):
    results: list[ScoreResult]
    total: int
    cached: int


class TokenRequest(BaseModel):
    api_key: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    redis_connected: bool


class ModelMetrics(BaseModel):
    accuracy: float | None = None
    n_samples: int | None = None
    feature_importance: list[dict] | None = None
