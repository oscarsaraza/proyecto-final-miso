"""Pruebas del motor actuarial de cotización y degradación (TC-S1-05, TC-S1-06)."""
import pytest
from app.modules.rating.models import QuoteRequest
from app.modules.rating.service import RatingService, rating_service


@pytest.mark.unit
def test_rating_service_raises_not_implemented():
    """Valida que el servicio base tenga firma de calculate_quote y lance NotImplementedError antes de HU-WEB-03."""
    request = QuoteRequest(
        document_type="CC",
        document_number="1020304050",
        birth_date="1990-05-15",
        insured_amount=100000000.0,
    )
    with pytest.raises(NotImplementedError):
        import asyncio
        asyncio.run(rating_service.calculate_quote(request))


@pytest.mark.unit
@pytest.mark.skip(reason="TDD: Se habilitará al implementar HU-WEB-03 (Tarificación en memoria)")
@pytest.mark.asyncio
async def test_rating_in_memory_latency_and_tiers():
    """TC-S1-05: Valida que la cotización en memoria se calcule en sub-milisegundos con 3 planes (ASR-01)."""
    pass


@pytest.mark.unit
@pytest.mark.skip(reason="TDD: Se habilitará al implementar HU-WEB-04 (Degradación elegante)")
@pytest.mark.asyncio
async def test_rating_fallback_on_bureau_timeout():
    """TC-S1-06: Valida que ante retardo > 400ms del buró se active degradación elegante (ASR-02 / HA-02)."""
    pass
