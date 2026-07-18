"""
Scoring engine extracted from ViviendaStateInvestor.
Rule-based multi-factor scoring with investor profile weights.
"""

from dataclasses import dataclass


@dataclass
class ScoringWeights:
    descuento: float = 1.2
    precio: float = 1.2
    liquidez: float = 1.0
    tamano: float = 1.0


DEFAULT_WEIGHTS = ScoringWeights()


def compute_score(
    precio_total: float,
    metros: float,
    precio_m2: float,
    precio_m2_barrio: float,
    weights: ScoringWeights | None = None,
) -> dict:
    """Compute investment score from property metrics."""
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # Score components
    if precio_m2_barrio > 0:
        diferencia_pct = (precio_m2_barrio - precio_m2) / precio_m2_barrio * 100
    else:
        diferencia_pct = 0

    score_descuento = max(0, min(diferencia_pct * 2, 40))

    if precio_m2_barrio > 0:
        ratio = precio_m2 / precio_m2_barrio
    else:
        ratio = 1

    if ratio < 0.85:
        score_precio = 25
    elif ratio < 0.95:
        score_precio = 15
    else:
        score_precio = 5

    if 50 <= metros <= 90:
        score_liquidez = 15
    elif 90 < metros <= 140:
        score_liquidez = 10
    else:
        score_liquidez = 5

    score_tamano = 10 if metros > 60 else 5

    # Weighted total
    score_raw = (
        score_descuento * weights.descuento
        + score_precio * weights.precio
        + score_liquidez * weights.liquidez
        + score_tamano * weights.tamano
    )

    max_possible = (
        40 * weights.descuento
        + 25 * weights.precio
        + 15 * weights.liquidez
        + 10 * weights.tamano
    )

    score_total = round((score_raw / max_possible) * 100, 2) if max_possible > 0 else 0

    # Rentabilidad
    if precio_m2_barrio > 0 and precio_total > 0:
        valor_mercado = precio_m2_barrio * metros
        rentabilidad = round(((valor_mercado - precio_total) / precio_total) * 100, 2)
    else:
        rentabilidad = 0

    # Decision
    if score_total >= 65 and rentabilidad >= 4:
        decision = "COMPRAR"
    elif score_total >= 45:
        decision = "NEGOCIAR"
    else:
        decision = "DESCARTAR"

    return {
        "score_total": score_total,
        "score_descuento": round(score_descuento, 2),
        "score_precio": score_precio,
        "score_liquidez": score_liquidez,
        "score_tamano": score_tamano,
        "decision": decision,
        "rentabilidad_estimada": rentabilidad,
    }
