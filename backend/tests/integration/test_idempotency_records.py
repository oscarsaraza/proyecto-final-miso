"""TC-S1-08: la clave de idempotencia es por socio (HU-WEB-06)."""
import pytest
from pydantic import BaseModel

from app.core.idempotency import find_response, save_response


class Charge(BaseModel):
    policy_number: str = "POL-2026-00001"


@pytest.mark.integration
async def test_la_misma_clave_de_otro_socio_es_otra_operacion(postgres_session):
    """S8-Arq §4.2: la clave primaria es (partner_id, idempotency_key); el canal web usa un solo socio."""
    save_response(postgres_session, "socio-a", "clave-1", Charge(), 402, {"detail": "Pago rechazado."})
    await postgres_session.commit()
    postgres_session.expunge_all()

    found = [await find_response(postgres_session, partner, "clave-1", Charge()) for partner in ("socio-a", "socio-b")]

    assert [record and record.response_status for record in found] == [402, None]
