"""TC-S1-07: emisión de la póliza contra PostgreSQL (HU-WEB-05)."""
import asyncio
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.core.outbox import OutboxMessageDB
from app.core.security import create_access_token
from app.modules.policy.models import PolicyDB
from app.modules.policy.service import one_year_after, policy_service

EXPIRED_DETAIL = "La cotización venció: recalcule la tarifa con datos actuales."


def advisor_headers() -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject='asesor@solventa.com', role='advisor')}"}


async def quote(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/experience/quotes",
        headers=advisor_headers(),
        json={"document_type": "CC", "document_number": "1020304050", "birth_date": "1990-05-15", "insured_amount": 1e8},
    )
    return response.json()


async def issue(client: AsyncClient, quote_id: str, tier: str = "standard"):
    body = {"quote_id": quote_id, "tier": tier}
    return await client.post("/api/v1/experience/policies", headers=advisor_headers(), json=body)


async def stored(session) -> tuple:
    """Pólizas y eventos guardados; la base se recrea en cada prueba."""
    return (
        await session.scalar(select(func.count()).select_from(PolicyDB)),
        await session.scalar(select(func.count()).select_from(OutboxMessageDB)),
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "issued, expected", [("2028-02-28", "2029-02-28"), ("2028-02-29", "2029-02-28"), ("2028-03-01", "2029-03-01")]
)
def test_vigencia_de_un_anio_con_el_29_de_febrero(issued, expected):
    assert one_year_after(datetime.fromisoformat(issued)) == datetime.fromisoformat(expected)


@pytest.mark.integration
async def test_emite_la_poliza_del_plan_elegido_con_su_evento(async_client: AsyncClient, postgres_session):
    """TC-S1-07: póliza ISSUED numerada POL-YYYY-XXXXX, con el plan elegido, un año de vigencia y su evento PolicyIssued."""
    quoted = await quote(async_client)

    response = await issue(async_client, quoted["quote_id"], tier="premium")

    policy = response.json()
    issued_at = datetime.fromisoformat(policy["issued_at"])
    assert (response.status_code, policy["policy_number"], policy["status"]) == (
        200, f"POL-{issued_at.year}-00001", "ISSUED"
    )
    assert policy["conditions"] == next(tier for tier in quoted["tiers"] if tier["tier"] == "premium")
    assert (policy["insured_document"], datetime.fromisoformat(policy["valid_until"])) == (
        quoted["document_number"], one_year_after(issued_at)
    )
    event = await postgres_session.scalar(select(OutboxMessageDB))
    assert (event.aggregate_id, event.event_type, event.status) == (policy["policy_number"], "PolicyIssued", "PENDING")


@pytest.mark.integration
@pytest.mark.parametrize(
    "offset, status_code, detail, saved",
    [(-1, 200, None, (1, 1)), (0, 409, EXPIRED_DETAIL, (0, 0)), (1, 409, EXPIRED_DETAIL, (0, 0))],
)
async def test_solo_emite_cotizaciones_vigentes(
    async_client: AsyncClient, postgres_session, monkeypatch, offset, status_code, detail, saved
):
    """TC-S1-07: la cotización vence en su expires_at exacto; vencida, se rechaza sin guardar nada y pide recalcular."""
    quoted = await quote(async_client)
    expires_at = datetime.fromisoformat(quoted["expires_at"])
    monkeypatch.setattr(policy_service, "now", lambda: expires_at + timedelta(microseconds=offset))

    response = await issue(async_client, quoted["quote_id"])

    observed = (response.status_code, response.json().get("detail"), await stored(postgres_session))
    assert observed == (status_code, detail, saved)


@pytest.mark.integration
async def test_repetir_la_emision_devuelve_la_misma_poliza_aunque_la_cotizacion_haya_vencido(
    async_client: AsyncClient, postgres_session, monkeypatch
):
    """TC-S1-07: el reintento, aun con otro plan o con la cotización ya vencida, devuelve la póliza original sin escribir."""
    quoted = await quote(async_client)
    first = (await issue(async_client, quoted["quote_id"])).json()
    monkeypatch.setattr(policy_service, "now", lambda: datetime.fromisoformat(quoted["expires_at"]) + timedelta(days=1))

    again = await issue(async_client, quoted["quote_id"], tier="premium")

    assert (again.status_code, again.json(), await stored(postgres_session)) == (200, first, (1, 1))


@pytest.mark.integration
async def test_diez_emisiones_simultaneas_crean_una_sola_poliza(async_client: AsyncClient, postgres_session):
    """TC-S1-07: 10 peticiones simultáneas con el mismo quote_id dejan una póliza y un evento, y todas reciben esa póliza."""
    quoted = await quote(async_client)

    responses = await asyncio.gather(*(issue(async_client, quoted["quote_id"]) for _ in range(10)))

    assert [response.status_code for response in responses] == [200] * 10
    assert len({response.json()["policy_number"] for response in responses}) == 1
    assert await stored(postgres_session) == (1, 1)


@pytest.mark.integration
async def test_cotizacion_inexistente_responde_404(async_client: AsyncClient, postgres_session):
    response = await issue(async_client, "QUO-NOEXISTE0000")

    assert (response.status_code, response.json()["detail"]) == (404, "La cotización no existe.")


@pytest.mark.integration
async def test_si_el_evento_no_se_guarda_tampoco_queda_la_poliza(async_client: AsyncClient, postgres_session):
    """HA-11: la póliza y su evento se guardan en la misma transacción."""
    quoted = await quote(async_client)
    await postgres_session.execute(
        text("ALTER TABLE outbox ADD CONSTRAINT bloquea_eventos CHECK (event_type <> 'PolicyIssued')")
    )
    await postgres_session.commit()

    with pytest.raises(IntegrityError):
        await issue(async_client, quoted["quote_id"])

    assert await stored(postgres_session) == (0, 0)
