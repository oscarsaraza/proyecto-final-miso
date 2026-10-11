"""Pruebas del motor actuarial de cotización y degradación (TC-S1-05, TC-S1-06)."""
import time
from datetime import date

import pytest

from app.modules.rating.models import PlanTier, QuoteRequest
from app.modules.rating.service import (
    BASE_MONTHLY_RATE,
    RatingService,
    age_multiplier,
    age_on,
    build_breakdown,
    score_multiplier,
)

TODAY = date(2026, 10, 9)


def make_request(**overrides) -> QuoteRequest:
    data = {
        "document_type": "CC",
        "document_number": "1020304050",
        "birth_date": "1990-05-15",
        "insured_amount": 100_000_000.0,
        "occupation_risk": 1,
    }
    data.update(overrides)
    return QuoteRequest(**data)


def make_service(score: int = 700) -> RatingService:
    async def fixed_score(request, delay):
        return score

    return RatingService(score_provider=fixed_score, today=lambda: TODAY)


@pytest.mark.unit
async def test_tc_s1_05_cotizacion_con_tres_planes_y_desglose():
    """TC-S1-05: tres planes con su desglose por factor (ASR-01)."""
    quote = await make_service().calculate_quote(make_request())

    assert [t.tier for t in quote.tiers] == [PlanTier.BASIC, PlanTier.STANDARD, PlanTier.PREMIUM]
    assert quote.status == "active"
    assert quote.quote_id.startswith("QUO-")
    for tier in quote.tiers:
        assert [f.code for f in tier.breakdown] == ["base_rate", "age", "occupation", "payment_history", "plan"]
        assert tier.annual_premium == tier.monthly_premium * 12


@pytest.mark.unit
async def test_hu_web_03_el_desglose_suma_exactamente_la_prima():
    quote = await make_service(score=820).calculate_quote(make_request(birth_date="1970-01-01", occupation_risk=4))

    for tier in quote.tiers:
        assert sum(f.amount for f in tier.breakdown) == tier.monthly_premium


@pytest.mark.unit
def test_hu_web_03_tarifa_base_proporcional_a_la_suma_asegurada():
    breakdown = build_breakdown(100_000_000, age=35, occupation_risk=1, score=700, tier=PlanTier.STANDARD)

    assert breakdown[0].amount == round(100_000_000 * BASE_MONTHLY_RATE)
    assert all(f.amount == 0 for f in breakdown[1:])


@pytest.mark.unit
def test_hu_web_03_perfil_de_mayor_riesgo_muestra_aportes_positivos():
    breakdown = {f.code: f for f in build_breakdown(100_000_000, 55, 3, 450, PlanTier.PREMIUM)}

    assert breakdown["age"].amount > 0
    assert breakdown["occupation"].amount > 0
    assert breakdown["payment_history"].amount > 0
    assert breakdown["plan"].amount > 0
    assert breakdown["age"].label == "Ajuste por edad (55 años)"


@pytest.mark.unit
def test_hu_web_03_buen_perfil_muestra_descuentos_negativos():
    breakdown = {f.code: f for f in build_breakdown(100_000_000, 25, 1, 850, PlanTier.BASIC)}

    assert breakdown["age"].amount < 0
    assert breakdown["payment_history"].amount < 0
    assert breakdown["plan"].amount < 0


@pytest.mark.unit
@pytest.mark.parametrize(
    "age, expected", [(18, 0.92), (30, 0.92), (31, 1.0), (40, 1.0), (41, 1.18), (50, 1.18), (51, 1.42), (75, 1.42)]
)
def test_bandas_de_edad(age, expected):
    assert age_multiplier(age) == expected


@pytest.mark.unit
@pytest.mark.parametrize("score, expected", [(900, 0.9), (800, 0.9), (700, 1.0), (650, 1.0), (520, 1.15), (300, 1.3)])
def test_bandas_de_puntaje(score, expected):
    assert score_multiplier(score) == expected


@pytest.mark.unit
def test_edad_cumplida_segun_fecha_de_nacimiento():
    assert age_on(date(1990, 10, 9), TODAY) == 36
    assert age_on(date(1990, 10, 10), TODAY) == 35


@pytest.mark.unit
async def test_coberturas_crecen_con_el_plan():
    quote = await make_service().calculate_quote(make_request())

    assert [len(t.coverages) for t in quote.tiers] == [1, 2, 3]


@pytest.mark.unit
def test_tc_s1_05_calculo_en_memoria_es_inmediato():
    """TC-S1-05: el cálculo de los tres planes no depende de E/S (ASR-01)."""
    start = time.perf_counter()
    for _ in range(100):
        for tier in PlanTier:
            build_breakdown(150_000_000, 42, 2, 700, tier)
    elapsed_per_quote_ms = (time.perf_counter() - start) * 1000 / 100

    assert elapsed_per_quote_ms < 5


@pytest.mark.unit
@pytest.mark.skip(reason="TDD: Se habilitará al implementar HU-WEB-04 (Degradación elegante)")
@pytest.mark.asyncio
async def test_rating_fallback_on_bureau_timeout():
    """TC-S1-06: Valida que ante retardo > 400ms del buró se active degradación elegante (ASR-02 / HA-02)."""
    pass
