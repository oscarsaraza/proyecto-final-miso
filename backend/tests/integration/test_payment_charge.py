"""TC-S1-08: cobro de la prima sin duplicar el cargo, contra PostgreSQL (HU-WEB-06)."""
import asyncio
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.core.idempotency import IdempotencyRecordDB
from app.core.outbox import OutboxMessageDB
from app.core.security import create_access_token
from app.modules.payments.gateway import GatewayUnavailableError, SimulatedGateway
from app.modules.payments.models import PaymentTransactionDB
from app.modules.payments.service import payment_service
from app.modules.policy.models import PolicyDB

DECLINED = "Pago rechazado: fondos insuficientes. Intente con otro medio de pago."
DRAINED = "tok_insufficient_funds"
# Estado de la póliza, estados de sus cobros, eventos PaymentApproved y claves guardadas.
UNPAID = ("ISSUED", [], 0, 0)
PAID = ("ACTIVE", ["APPROVED"], 1, 1)


def advisor_headers(**extra) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject='asesor@solventa.com', role='advisor')}", **extra}


async def issued_policy(client: AsyncClient) -> dict:
    quote = await client.post(
        "/api/v1/experience/quotes",
        headers=advisor_headers(),
        json={"document_type": "CC", "document_number": "1020304050", "birth_date": "1990-05-15", "insured_amount": 1e8},
    )
    body = {"quote_id": quote.json()["quote_id"], "tier": "standard"}
    return (await client.post("/api/v1/experience/policies", headers=advisor_headers(), json=body)).json()


async def charge(client: AsyncClient, policy: dict, key: str = "clave-1", **overrides):
    """Cobra la prima mensual de la póliza por PSE; cada prueba cambia solo la clave o el campo que le interesa."""
    body = {
        "policy_number": policy["policy_number"],
        "amount": policy["conditions"]["monthly_premium"],
        "payment_method": "PSE",
        "token_or_account": "tok_pse_bancolombia",
        **overrides,
    }
    headers = advisor_headers(**{"Idempotency-Key": key})
    return await client.post("/api/v1/experience/payments/charge", headers=headers, json=body)


async def stored(session, policy: dict) -> tuple:
    """Lo que quedó en la base para la póliza; la base se recrea en cada prueba."""
    number = policy["policy_number"]
    payments = select(PaymentTransactionDB.status).where(PaymentTransactionDB.policy_number == number)
    events = select(func.count()).select_from(OutboxMessageDB).where(OutboxMessageDB.event_type == "PaymentApproved")
    return (
        await session.scalar(select(PolicyDB.status).where(PolicyDB.policy_number == number)),
        sorted((await session.scalars(payments)).all()),
        await session.scalar(events),
        await session.scalar(select(func.count()).select_from(IdempotencyRecordDB)),
    )


@pytest.fixture(autouse=True)
def fresh_gateway(monkeypatch):
    """La pasarela recuerda cada clave cobrada; cada prueba empieza con una nueva."""
    monkeypatch.setattr(payment_service, "gateway", SimulatedGateway())


class CutAfterCharge(SimulatedGateway):
    """Cobra y, la primera vez, pierde la respuesta como si se cortara la red."""

    def __init__(self):
        super().__init__()
        self.cut = True

    async def charge(self, idempotency_key: str, amount: float, token: str):
        result = await super().charge(idempotency_key, amount, token)
        if self.cut:
            self.cut = False
            raise GatewayUnavailableError()
        return result


@pytest.mark.unit
async def test_la_pasarela_simulada_no_vuelve_a_cobrar_la_misma_clave():
    """Rechaza el token sin fondos y, con una clave ya cobrada, repite su resultado aunque cambie el token."""
    gateway = SimulatedGateway()

    first = [await gateway.charge(key, 1.0, token) for key, token in [("clave-1", "tok_visa"), ("clave-2", DRAINED)]]
    again = [await gateway.charge(key, 1.0, token) for key, token in [("clave-1", DRAINED), ("clave-2", "tok_visa")]]

    assert first == again == [None, "fondos insuficientes"]


@pytest.mark.integration
async def test_cobro_aprobado_activa_la_poliza_con_su_recibo_y_su_evento(async_client: AsyncClient, postgres_session):
    """TC-S1-08: el cobro queda asociado a la póliza, que pasa a ACTIVE, y deja PaymentApproved para el correo."""
    policy = await issued_policy(async_client)

    response = await charge(async_client, policy)

    receipt = response.json()
    year = datetime.fromisoformat(receipt["created_at"]).year
    assert (response.status_code, receipt["status"], receipt["receipt_number"], receipt["amount"]) == (
        200, "APPROVED", f"REC-{year}-00001", policy["conditions"]["monthly_premium"]
    )
    assert (receipt["policy_number"], receipt["idempotency_key"]) == (policy["policy_number"], "clave-1")
    assert await stored(postgres_session, policy) == PAID
    event = select(OutboxMessageDB.payload).where(OutboxMessageDB.event_type == "PaymentApproved")
    assert await postgres_session.scalar(event) == receipt


@pytest.mark.integration
async def test_reintentar_con_la_misma_clave_devuelve_el_mismo_recibo_sin_otro_cargo(
    async_client: AsyncClient, postgres_session
):
    """TC-S1-08: si la respuesta se pierde en la red, el reintento con la misma clave la recupera."""
    policy = await issued_policy(async_client)
    first = await charge(async_client, policy)

    again = await charge(async_client, policy)

    assert (again.status_code, again.json(), await stored(postgres_session, policy)) == (200, first.json(), PAID)


@pytest.mark.integration
@pytest.mark.parametrize(
    "key, detail",
    [("clave-1", "La clave de idempotencia ya se usó con otra solicitud."), ("clave-2", "La póliza ya está pagada.")],
)
async def test_la_poliza_pagada_no_se_vuelve_a_cobrar(async_client: AsyncClient, postgres_session, key, detail):
    """HA-11: la misma clave con otro cuerpo, u otra clave sobre la póliza pagada, es un conflicto sin cargo."""
    policy = await issued_policy(async_client)
    await charge(async_client, policy)

    response = await charge(async_client, policy, key, payment_method="CARD", token_or_account="tok_visa")

    assert (response.status_code, response.json()["detail"], await stored(postgres_session, policy)) == (
        409, detail, PAID
    )


@pytest.mark.integration
async def test_cobro_rechazado_deja_la_poliza_pendiente_y_se_repite_con_la_misma_clave(
    async_client: AsyncClient, postgres_session
):
    """TC-S1-08: el rechazo informa el motivo y no activa la póliza; la misma clave repite el rechazo sin otro intento."""
    policy = await issued_policy(async_client)

    responses = [await charge(async_client, policy, token_or_account=DRAINED) for _ in range(2)]

    assert [(response.status_code, response.json()["detail"]) for response in responses] == [(402, DECLINED)] * 2
    assert await stored(postgres_session, policy) == ("ISSUED", ["DECLINED"], 0, 1)


@pytest.mark.integration
@pytest.mark.parametrize("delta, status_code, saved", [(-1, 422, UNPAID), (0, 200, PAID), (1, 422, UNPAID)])
async def test_solo_cobra_la_prima_mensual_exacta(async_client: AsyncClient, postgres_session, delta, status_code, saved):
    policy = await issued_policy(async_client)

    response = await charge(async_client, policy, amount=policy["conditions"]["monthly_premium"] + delta)

    assert (response.status_code, await stored(postgres_session, policy)) == (status_code, saved)


@pytest.mark.integration
async def test_poliza_inexistente_responde_404(async_client: AsyncClient, postgres_session):
    response = await charge(async_client, {"policy_number": "POL-2026-99999", "conditions": {"monthly_premium": 1.0}})

    assert (response.status_code, response.json()["detail"]) == (404, "La póliza no existe.")


@pytest.mark.integration
@pytest.mark.parametrize(
    "keys, codes",
    [(["clave-1"] * 10, [200] * 10), ([f"clave-{i}" for i in range(10)], [200] + [409] * 9)],
    ids=["misma-clave", "claves-distintas"],
)
async def test_diez_cobros_simultaneos_dejan_un_solo_cargo(
    async_client: AsyncClient, postgres_session, keys, codes
):
    """ASR-05: con la misma clave todos reciben el mismo recibo; con claves distintas uno cobra y el resto, 409."""
    policy = await issued_policy(async_client)

    responses = await asyncio.gather(*(charge(async_client, policy, key) for key in keys))

    assert sorted(response.status_code for response in responses) == codes
    assert len({response.text for response in responses if response.status_code == 200}) == 1
    assert await stored(postgres_session, policy) == PAID


@pytest.mark.integration
async def test_corte_despues_de_cobrar_y_reintento_con_la_misma_clave(
    async_client: AsyncClient, postgres_session, monkeypatch
):
    """S8-HU p14: la pasarela cobra y se corta; no queda nada a medias y el reintento termina el mismo cobro."""
    policy = await issued_policy(async_client)
    monkeypatch.setattr(payment_service, "gateway", CutAfterCharge())

    cut = await charge(async_client, policy)
    after_cut = await stored(postgres_session, policy)
    retry = await charge(async_client, policy)

    assert (cut.status_code, after_cut) == (502, UNPAID)
    assert (retry.status_code, await stored(postgres_session, policy)) == (200, PAID)


@pytest.mark.integration
async def test_si_el_evento_no_se_guarda_no_queda_cobro_ni_poliza_pagada(async_client: AsyncClient, postgres_session):
    """HA-11: el cobro, la póliza, la clave y el evento se confirman en una sola transacción."""
    policy = await issued_policy(async_client)
    await postgres_session.execute(
        text("ALTER TABLE outbox ADD CONSTRAINT bloquea_cobros CHECK (event_type <> 'PaymentApproved')")
    )
    await postgres_session.commit()

    with pytest.raises(IntegrityError):
        await charge(async_client, policy)

    assert await stored(postgres_session, policy) == UNPAID
