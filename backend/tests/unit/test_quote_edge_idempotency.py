"""Pruebas unitarias y de integración de idempotencia B2B en Quote Edge (HU-WEB-11, #179, #180)."""
import asyncio
from datetime import datetime, timedelta, timezone
import time
import pytest
from httpx import AsyncClient

from app.core.security import get_password_hash
from app.modules.rating.models import PartnerDB, PartnerStatus


QUOTE_PAYLOAD = {
    "document_type": "CC",
    "document_number": "1020304050",
    "birth_date": "1990-05-15",
    "insured_amount": 150000000.0,
    "city": "Bogota",
    "occupation_risk": 2,
}


async def _obtain_partner_token(
    client: AsyncClient,
    client_id: str = "banco_aliado",
    client_secret: str = "AliadoSecret2026*",
) -> str:
    resp = await client.post(
        "/api/v1/quote-edge/auth/token",
        json={"client_id": client_id, "client_secret": client_secret},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_quote_edge_missing_idempotency_key(async_client: AsyncClient):
    """TC-03 / AC-03: Rechazo con 400 Bad Request cuando el encabezado Idempotency-Key falta o está vacío."""
    token = await _obtain_partner_token(async_client)
    auth_header = {"Authorization": f"Bearer {token}"}

    # 1. Sin encabezado Idempotency-Key
    resp_missing = await async_client.post(
        "/api/v1/quote-edge/quotes",
        headers=auth_header,
        json=QUOTE_PAYLOAD,
    )
    assert resp_missing.status_code == 400
    assert "Idempotency-Key" in resp_missing.json()["detail"]

    # 2. Encabezado Idempotency-Key compuesto únicamente de espacios en blanco
    resp_empty = await async_client.post(
        "/api/v1/quote-edge/quotes",
        headers={**auth_header, "Idempotency-Key": "    "},
        json=QUOTE_PAYLOAD,
    )
    assert resp_empty.status_code == 400
    assert "Idempotency-Key" in resp_empty.json()["detail"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_idempotent_quote_retry_success(
    async_client: AsyncClient,
    test_db_session,
):
    """TC-01 / AC-01: Reintento con la misma clave y contenido idéntico devuelve la misma cotización sin duplicar registros."""
    token = await _obtain_partner_token(async_client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "key-idempotent-success-01",
    }

    # Solicitud inicial
    resp1 = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)
    assert resp1.status_code == 200
    data1 = resp1.json()
    quote_id_1 = data1["quote_id"]

    partner = test_db_session.partners_by_id["banco-aliado-1"]
    quota_after_first = partner.quota_used
    assert quota_after_first >= 1
    total_quotes_first = len(test_db_session.quotes)

    # Reintento con la misma clave y payload
    resp2 = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)
    assert resp2.status_code == 200
    data2 = resp2.json()

    # Verifica que la respuesta es idéntica
    assert data2["quote_id"] == quote_id_1
    assert data2["partner_id"] == data1["partner_id"]
    assert data2["tiers"] == data1["tiers"]

    # Verifica que NO se creó un nuevo registro de cotización ni se incrementó la cuota
    assert len(test_db_session.quotes) == total_quotes_first
    assert partner.quota_used == quota_after_first


@pytest.mark.unit
@pytest.mark.asyncio
async def test_idempotent_quote_payload_conflict(async_client: AsyncClient):
    """TC-02 / AC-02: Rechazo con 409 Conflict si se reutiliza una clave activa con un payload diferente."""
    token = await _obtain_partner_token(async_client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "key-conflict-test-02",
    }

    # Primera solicitud con payload A
    resp1 = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)
    assert resp1.status_code == 200

    # Segunda solicitud con la misma clave pero payload B modificado
    altered_payload = {**QUOTE_PAYLOAD, "insured_amount": 250000000.0}
    resp2 = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=altered_payload)
    assert resp2.status_code == 409
    assert "Conflicto de idempotencia" in resp2.json()["detail"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_idempotency_key_expiration_after_24_hours(
    async_client: AsyncClient,
    test_db_session,
):
    """TC-04 / AC-04: Una clave usada hace más de 24 horas expira y se procesa como una solicitud nueva."""
    token = await _obtain_partner_token(async_client)
    key = "key-expirable-test-04"
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": key,
    }

    # 1. Petición inicial
    resp1 = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)
    assert resp1.status_code == 200
    first_quote_id = resp1.json()["quote_id"]

    # 2. Simular antigüedad de 25 horas en el registro de idempotencia
    rec = test_db_session.idempotency_records[("banco-aliado-1", key)]
    rec.created_at = datetime.now(timezone.utc) - timedelta(hours=25)

    # 3. Reutilizar la clave vencida
    resp2 = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)
    assert resp2.status_code == 200
    second_quote_id = resp2.json()["quote_id"]

    # Debe generar una nueva cotización (distinto quote_id)
    assert second_quote_id != first_quote_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_idempotency_multitenant_isolation(
    async_client: AsyncClient,
    test_db_session,
):
    """TC-05 / AC-05: Dos socios que utilizan la misma clave de idempotencia se aíslan sin colisión ni conflicto."""
    # Crear segundo socio activo
    second_partner = PartnerDB(
        partner_id="socio-cooperativa-2",
        client_id="socio_coop",
        client_secret_hash=get_password_hash("CoopSecret2026*"),
        name="Cooperativa Aliada",
        status=PartnerStatus.ACTIVE.value,
        quota_limit=20000,
        quota_used=0,
    )
    test_db_session.add(second_partner)

    token_p1 = await _obtain_partner_token(async_client, "banco_aliado", "AliadoSecret2026*")
    token_p2 = await _obtain_partner_token(async_client, "socio_coop", "CoopSecret2026*")

    shared_key = "idempotency-key-shared-between-partners"

    # Socio 1 emite cotización
    resp_p1 = await async_client.post(
        "/api/v1/quote-edge/quotes",
        headers={"Authorization": f"Bearer {token_p1}", "Idempotency-Key": shared_key},
        json=QUOTE_PAYLOAD,
    )
    assert resp_p1.status_code == 200
    data_p1 = resp_p1.json()

    # Socio 2 emite cotización con la misma clave pero su propio token y diferente documento
    payload_p2 = {**QUOTE_PAYLOAD, "document_number": "8888777766"}
    resp_p2 = await async_client.post(
        "/api/v1/quote-edge/quotes",
        headers={"Authorization": f"Bearer {token_p2}", "Idempotency-Key": shared_key},
        json=payload_p2,
    )
    assert resp_p2.status_code == 200
    data_p2 = resp_p2.json()

    # Verificación de aislamiento
    assert data_p1["partner_id"] == "banco-aliado-1"
    assert data_p2["partner_id"] == "socio-cooperativa-2"
    assert data_p1["quote_id"] != data_p2["quote_id"]
    assert ("banco-aliado-1", shared_key) in test_db_session.idempotency_records
    assert ("socio-cooperativa-2", shared_key) in test_db_session.idempotency_records


@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_idempotent_quotes(
    async_client: AsyncClient,
    test_db_session,
):
    """TC-06 / AC-01: Reintentos concurrentes con la misma clave devuelven la misma cotización sin duplicados."""
    token = await _obtain_partner_token(async_client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "concurrent-quote-key-06",
    }

    # Emitir solicitud inicial para fijar el registro
    init_resp = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)
    assert init_resp.status_code == 200
    expected_quote_id = init_resp.json()["quote_id"]
    quotes_count_before = len(test_db_session.quotes)

    # Disparar 5 reintentos en paralelo
    async def make_request():
        return await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)

    results = await asyncio.gather(*[make_request() for _ in range(5)])

    for r in results:
        assert r.status_code == 200
        assert r.json()["quote_id"] == expected_quote_id

    # La cantidad de cotizaciones en base de datos no se incrementó
    assert len(test_db_session.quotes) == quotes_count_before


@pytest.mark.unit
@pytest.mark.asyncio
async def test_idempotent_quote_latency_performance(async_client: AsyncClient):
    """TC-07 / QR-01: Reintento idempotente resuelto desde persistencia con baja latencia (<50 ms)."""
    token = await _obtain_partner_token(async_client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "perf-quote-key-07",
    }

    # Primera llamada
    resp1 = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)
    assert resp1.status_code == 200

    # Segunda llamada (reintento) midiendo tiempo
    start = time.perf_counter()
    resp2 = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert resp2.status_code == 200
    assert resp2.json()["quote_id"] == resp1.json()["quote_id"]
    assert elapsed_ms < 50.0  # Menos de 50 ms en local
