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
    model_config = {"protected_namespaces": ()}

    status: str
    model_loaded: bool
    redis_connected: bool


class ModelMetrics(BaseModel):
    accuracy: float | None = None
    n_samples: int | None = None
    n_train: int | None = None
    n_test: int | None = None
    feature_importance: list[dict] | None = None
    classification_report: dict | None = None
    confusion_matrix: list[list[int]] | None = None


class PredictRequest(BaseModel):
    score_descuento: float = Field(..., ge=0, le=40)
    score_precio: float = Field(..., ge=0, le=25)
    score_liquidez: float = Field(..., ge=0, le=15)
    score_tamano: float = Field(..., ge=0, le=10)
    precio_total: float = Field(..., gt=0)
    metros: float = Field(..., gt=0)
    precio_m2: float = Field(..., gt=0)
    rentabilidad_estimada: float


class PredictResponse(BaseModel):
    prediction: str
    confidence: float
    probabilities: dict[str, float]


class TrainRecord(BaseModel):
    score_descuento: float
    score_precio: float
    score_liquidez: float
    score_tamano: float
    precio_total: float
    metros: float
    precio_m2: float
    rentabilidad_estimada: float
    decision: str = Field(..., pattern="^(COMPRAR|NEGOCIAR|DESCARTAR)$")


class TrainRequest(BaseModel):
    records: list[TrainRecord] = Field(..., min_length=10, max_length=100000)


class TrainResponse(BaseModel):
    accuracy: float
    n_samples: int
    n_train: int
    n_test: int
    feature_importance: list[dict]
