"""Pruebas de integración HTTP de los endpoints B2B de emisión y consulta de pólizas (HU-WEB-14)."""
from datetime import datetime, timedelta, timezone
import time
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_partner_access_token
from app.modules.rating.models import PartnerDB, PartnerStatus, QuoteDB


QUOTE_PAYLOAD = {
    "document_type": "CC",
    "document_number": "1020304050",
    "birth_date": "1990-05-15",
    "insured_amount": 100000000.0,
    "city": "Bogota",
    "occupation_risk": 1,
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


async def _create_partner_quote(client: AsyncClient, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/v1/quote-edge/quotes", headers=headers, json=QUOTE_PAYLOAD)
    assert resp.status_code == 200
    return resp.json()["quote_id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_issue_partner_policy_success(async_client: AsyncClient):
    """TC-01: Emisión exitosa de póliza digital desde el canal del socio B2B."""
    token = await _obtain_partner_token(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    quote_id = await _create_partner_quote(async_client, token)

    payload = {
        "quote_id": quote_id,
        "tier": "standard",
        "beneficiaries": [{"name": "Carlos Gomez", "relationship": "Hijo", "percentage": 100}],
    }
    resp = await async_client.post("/api/v1/quote-edge/policies", headers=headers, json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["policy_number"].startswith("POL-")
    assert data["quote_id"] == quote_id
    assert data["partner_id"] == "banco-aliado-1"
    assert data["insured_document"] == "1020304050"
    assert data["status"] == "ISSUED"
    assert data["conditions"]["tier"] == "standard"
    assert data["valid_until"] > data["issued_at"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_issue_policy_cross_tenant_forbidden(async_client: AsyncClient, test_db_session):
    """TC-02: Rechazo con 404 ante intento de emitir póliza con cotización de otro socio."""
    # Socio 1 crea cotización
    token_1 = await _obtain_partner_token(async_client)
    quote_id_1 = await _create_partner_quote(async_client, token_1)

    # Creamos un segundo socio en sesión
    second_partner = PartnerDB(
        partner_id="socio-segundo-2",
        client_id="socio_segundo",
        client_secret_hash="fake-hash",
        name="Segundo Socio",
        status=PartnerStatus.ACTIVE.value,
        quota_limit=1000,
        quota_used=0,
    )
    test_db_session.add(second_partner)

    token_2 = create_partner_access_token(client_id="socio_segundo", partner_id="socio-segundo-2")
    headers_2 = {"Authorization": f"Bearer {token_2}"}

    # Socio 2 intenta emitir la cotización del Socio 1 -> 404 Not Found
    payload = {"quote_id": quote_id_1, "tier": "standard"}
    resp = await async_client.post("/api/v1/quote-edge/policies", headers=headers_2, json=payload)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Cotización no encontrada"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_issue_policy_idempotency(async_client: AsyncClient):
    """TC-03: Emisión idempotente ante reintentos con la misma cotización."""
    token = await _obtain_partner_token(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    quote_id = await _create_partner_quote(async_client, token)

    payload = {"quote_id": quote_id, "tier": "standard"}
    resp1 = await async_client.post("/api/v1/quote-edge/policies", headers=headers, json=payload)
    resp2 = await async_client.post("/api/v1/quote-edge/policies", headers=headers, json=payload)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["policy_number"] == resp2.json()["policy_number"]
    assert resp1.json()["issued_at"] == resp2.json()["issued_at"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_policy_cross_tenant_not_found(async_client: AsyncClient, test_db_session):
    """TC-04: Consulta de detalle confinado al socio; retorna 404 ante pólizas de otros socios."""
    token_1 = await _obtain_partner_token(async_client)
    headers_1 = {"Authorization": f"Bearer {token_1}"}
    quote_id = await _create_partner_quote(async_client, token_1)

    issue_resp = await async_client.post(
        "/api/v1/quote-edge/policies",
        headers=headers_1,
        json={"quote_id": quote_id, "tier": "standard"},
    )
    assert issue_resp.status_code == 200
    policy_number = issue_resp.json()["policy_number"]

    # Consulta propia -> 200 OK
    get_ok = await async_client.get(f"/api/v1/quote-edge/policies/{policy_number}", headers=headers_1)
    assert get_ok.status_code == 200
    assert get_ok.json()["policy_number"] == policy_number

    # Socio 2 intenta consultar la póliza de Socio 1 -> 404 Not Found
    second_partner = PartnerDB(
        partner_id="socio-segundo-2",
        client_id="socio_segundo",
        client_secret_hash="fake-hash",
        name="Segundo Socio",
        status=PartnerStatus.ACTIVE.value,
        quota_limit=1000,
        quota_used=0,
    )
    test_db_session.add(second_partner)

    token_2 = create_partner_access_token(client_id="socio_segundo", partner_id="socio-segundo-2")
    headers_2 = {"Authorization": f"Bearer {token_2}"}
    get_foreign = await async_client.get(f"/api/v1/quote-edge/policies/{policy_number}", headers=headers_2)
    assert get_foreign.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_issue_expired_quote_rejected(async_client: AsyncClient, test_db_session):
    """TC-05: Rechazo con 409 Conflict si la cotización ya expiró."""
    token = await _obtain_partner_token(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    # Creamos manualmente una cotización expirada en el almacén
    now = datetime.now(timezone.utc)
    expired_quote = QuoteDB(
        quote_id="COT-EXP-B2B",
        partner_id="banco-aliado-1",
        document_number="1020304050",
        status="active",
        score_applied=700.0,
        tiers=[
            {
                "tier": "standard",
                "monthly_premium": 60000.0,
                "annual_premium": 720000.0,
                "coverages": [],
                "breakdown": [],
            }
        ],
        created_at=now - timedelta(hours=2),
        expires_at=now - timedelta(hours=1),
    )
    test_db_session.add(expired_quote)

    resp = await async_client.post(
        "/api/v1/quote-edge/policies",
        headers=headers,
        json={"quote_id": "COT-EXP-B2B", "tier": "standard"},
    )
    assert resp.status_code == 409
    assert "ha expirado" in resp.json()["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_policy_endpoints_unauthenticated(async_client: AsyncClient):
    """TC-06: Endpoints de pólizas rechazan peticiones sin token o con rol inválido."""
    advisor_token = create_access_token(subject="asesor@solventa.co", role="advisor")

    # Sin token
    r1 = await async_client.post("/api/v1/quote-edge/policies", json={"quote_id": "X", "tier": "standard"})
    assert r1.status_code == 401

    r2 = await async_client.get("/api/v1/quote-edge/policies/POL-2026-00001")
    assert r2.status_code == 401

    r3 = await async_client.get("/api/v1/quote-edge/policies")
    assert r3.status_code == 401

    # Con rol advisor en vez de partner
    bad_headers = {"Authorization": f"Bearer {advisor_token}"}
    r4 = await async_client.post(
        "/api/v1/quote-edge/policies",
        headers=bad_headers,
        json={"quote_id": "X", "tier": "standard"},
    )
    assert r4.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_partner_policies_isolated(async_client: AsyncClient, test_db_session):
    """TC-07: Listado histórico de pólizas confinado estrictamente al socio (CQRS)."""
    token_1 = await _obtain_partner_token(async_client)
    headers_1 = {"Authorization": f"Bearer {token_1}"}

    q1 = await _create_partner_quote(async_client, token_1)
    q2 = await _create_partner_quote(async_client, token_1)

    await async_client.post("/api/v1/quote-edge/policies", headers=headers_1, json={"quote_id": q1, "tier": "standard"})
    await async_client.post("/api/v1/quote-edge/policies", headers=headers_1, json={"quote_id": q2, "tier": "basic"})

    resp = await async_client.get("/api/v1/quote-edge/policies", headers=headers_1)
    assert resp.status_code == 200
    policies = resp.json()
    assert len(policies) >= 2
    for p in policies:
        assert p["partner_id"] == "banco-aliado-1"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_policy_issue_performance(async_client: AsyncClient):
    """TC-08: Medición de rendimiento en emisión y lectura CQRS bajo carga local."""
    token = await _obtain_partner_token(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    quote_id = await _create_partner_quote(async_client, token)

    start = time.perf_counter()
    resp = await async_client.post(
        "/api/v1/quote-edge/policies",
        headers=headers,
        json={"quote_id": quote_id, "tier": "standard"},
    )
    duration_ms = (time.perf_counter() - start) * 1000

    assert resp.status_code == 200
    assert duration_ms < 200.0, f"Emisión tardó {duration_ms:.2f} ms (esperado < 200 ms)"

    start_read = time.perf_counter()
    list_resp = await async_client.get("/api/v1/quote-edge/policies", headers=headers)
    read_duration_ms = (time.perf_counter() - start_read) * 1000

    assert list_resp.status_code == 200
    assert read_duration_ms < 100.0, f"Lectura CQRS tardó {read_duration_ms:.2f} ms (esperado < 100 ms)"
