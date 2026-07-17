from app.scoring import compute_score


def test_comprar_decision():
    """Property well below market price should be COMPRAR."""
    result = compute_score(
        precio_total=150000,
        metros=80,
        precio_m2=1875,
        precio_m2_barrio=3000,
    )
    assert result["decision"] == "COMPRAR"
    assert result["score_total"] > 60


def test_descartar_decision():
    """Property above market price should be DESCARTAR."""
    result = compute_score(
        precio_total=400000,
        metros=50,
        precio_m2=8000,
        precio_m2_barrio=3000,
    )
    assert result["decision"] == "DESCARTAR"
    assert result["score_total"] < 45


def test_score_range():
    """Score should always be between 0 and 100."""
    for precio in [100000, 200000, 500000]:
        result = compute_score(
            precio_total=precio,
            metros=70,
            precio_m2=precio / 70,
            precio_m2_barrio=3000,
        )
        assert 0 <= result["score_total"] <= 100


def test_liquidez_optimal():
    """50-90m² should get max liquidity score."""
    result = compute_score(
        precio_total=200000,
        metros=75,
        precio_m2=2666,
        precio_m2_barrio=3000,
    )
    assert result["score_liquidez"] == 15


def test_tamano_bonus():
    """Properties >60m² should get size bonus."""
    result = compute_score(
        precio_total=200000,
        metros=80,
        precio_m2=2500,
        precio_m2_barrio=3000,
    )
    assert result["score_tamano"] == 10


def test_rentabilidad_positive():
    """Property below barrio average should have positive rentabilidad."""
    result = compute_score(
        precio_total=180000,
        metros=75,
        precio_m2=2400,
        precio_m2_barrio=3000,
    )
    assert result["rentabilidad_estimada"] > 0
