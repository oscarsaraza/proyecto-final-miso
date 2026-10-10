"""Pruebas de integración del arnés técnico base: Health check (ALB), Root y Placeholders 501."""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    """Valida que el endpoint /health responda HTTP 200 con formato requerido por el AWS ALB (HA-09)."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Valida que el punto de entrada raíz responda correctamente."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["health"] == "/health"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unimplemented_endpoints_return_501(async_client: AsyncClient):
    """Valida que los endpoints de historias protegidas retornen HTTP 501 Not Implemented con rol advisor."""
    from app.core.security import create_access_token
    advisor_token = create_access_token(subject="asesor@solventa.com", role="advisor")
    auth_headers = {"Authorization": f"Bearer {advisor_token}"}

    # 1. Validación de cliente (HU-WEB-02)
    client_resp = await async_client.post(
        "/api/v1/experience/clients/validate",
        headers=auth_headers,
        json={
            "document_type": "CC",
            "document_number": "1020304050",
            "first_name": "Carlos",
            "last_name": "Perez",
            "birth_date": "1990-05-15",
            "email": "carlos@test.com",
            "phone": "3001234567",
        },
    )
    assert client_resp.status_code == 501

    # 2. Consentimiento (HU-WEB-01)
    consent_resp = await async_client.post(
        "/api/v1/experience/consent",
        headers=auth_headers,
        json={
            "document_number": "1020304050",
            "otp_code": "123456",
            "terms_accepted": True,
        },
    )
    assert consent_resp.status_code == 501

    # 3. Cotización (HU-WEB-03)
    quote_resp = await async_client.post(
        "/api/v1/experience/quotes",
        headers=auth_headers,
        json={
            "document_type": "CC",
            "document_number": "1020304050",
            "birth_date": "1990-05-15",
            "insured_amount": 100000000.0,
        },
    )
    assert quote_resp.status_code == 501

    # 4. Emisión de póliza (HU-WEB-05)
    policy_resp = await async_client.post(
        "/api/v1/experience/policies",
        headers=auth_headers,
        json={
            "quote_id": "QUO-1",
            "tier": "standard",
            "insured_document": "1020304050",
        },
    )
    assert policy_resp.status_code == 501

    # 5. Pago (HU-WEB-06)
    pay_headers = {**auth_headers, "Idempotency-Key": "key-123"}
    pay_resp = await async_client.post(
        "/api/v1/experience/payments/charge",
        headers=pay_headers,
        json={
            "quote_id": "QUO-1",
            "policy_number": "POL-1",
            "amount": 100000.0,
            "currency": "COP",
            "payment_method": "PSE",
            "token_or_account": "ACC1",
        },
    )
    assert pay_resp.status_code == 501


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quote_edge_unauthorized_and_unimplemented(async_client: AsyncClient):
    """Valida canal quote-edge B2B: 401 si falta X-Partner-Id, y 501 al invocar servicio no implementado."""
    quote_payload = {
        "document_type": "CC",
        "document_number": "1020304050",
        "birth_date": "1990-05-15",
        "insured_amount": 100000000.0,
    }
    # Sin cabecera -> 401
    resp_no_header = await async_client.post("/api/v1/quote-edge/quotes", json=quote_payload)
    assert resp_no_header.status_code == 401

    # Con cabecera -> 501
    resp_with_header = await async_client.post(
        "/api/v1/quote-edge/quotes",
        headers={"X-Partner-Id": "banco-aliado-1"},
        json=quote_payload,
    )
    assert resp_with_header.status_code == 501
