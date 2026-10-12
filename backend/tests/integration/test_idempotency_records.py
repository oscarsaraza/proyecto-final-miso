"""TC-S1-08: registro de idempotencia en PostgreSQL (HU-WEB-06)."""
import pytest
from pydantic import BaseModel

from app.core.idempotency import IdempotencyConflictError, find_response, save_response

DECLINED = {"detail": "Pago rechazado: fondos insuficientes."}


class Charge(BaseModel):
    policy_number: str = "POL-2026-00001"
    amount: float = 151000.0


async def saved_charge(session) -> None:
    """Guarda la respuesta de la clave «clave-1» del socio A y suelta la copia en memoria."""
    save_response(session, "socio-a", "clave-1", Charge(), 402, DECLINED)
    await session.commit()
    session.expunge_all()


@pytest.mark.integration
@pytest.mark.parametrize(
    "partner_id, idempotency_key, expected",
    [("socio-a", "clave-1", (402, DECLINED)), ("socio-a", "clave-2", None), ("socio-b", "clave-1", None)],
)
async def test_la_misma_clave_del_mismo_socio_devuelve_la_respuesta_guardada(
    postgres_session, partner_id, idempotency_key, expected
):
    await saved_charge(postgres_session)

    record = await find_response(postgres_session, partner_id, idempotency_key, Charge())

    assert (record and (record.response_status, record.response_body)) == expected


@pytest.mark.integration
async def test_la_misma_clave_con_otra_peticion_es_un_conflicto(postgres_session):
    """HA-11: reintentar con la misma clave y otro cuerpo se rechaza."""
    await saved_charge(postgres_session)

    with pytest.raises(IdempotencyConflictError):
        await find_response(postgres_session, "socio-a", "clave-1", Charge(amount=1.0))
