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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hu_web_01_registro_y_consulta_de_consentimiento(async_client: AsyncClient):
    """HU-WEB-01 / TC-S1-04: registro de consentimiento con hash SHA-256, consulta y validaciones."""
    from app.core.security import create_access_token
    advisor_token = create_access_token(subject="asesor@solventa.com", role="advisor")
    auth_headers = {"Authorization": f"Bearer {advisor_token}"}

    # 1. Registro exitoso
    consent_resp = await async_client.post(
        "/api/v1/experience/consent",
        headers=auth_headers,
        json={
            "document_number": "1020304050",
            "otp_code": "839201",
            "terms_accepted": True,
            "purpose": "Perfilamiento y cotización de seguro con Open Finance",
            "scope": "Historial crediticio y capacidad de pago",
            "validity_days": 30,
        },
    )
    assert consent_resp.status_code == 200
    consent_data = consent_resp.json()
    assert consent_data["status"] == "GRANTED"
    assert consent_data["document_number"] == "1020304050"
    assert len(consent_data["consent_hash"]) == 64
    assert consent_data["validity_days"] == 30

    # 2. Consulta de consentimiento otorgado
    get_consent_resp = await async_client.get(
        "/api/v1/experience/consent/1020304050",
        headers=auth_headers,
    )
    assert get_consent_resp.status_code == 200
    assert get_consent_resp.json()["consent_id"] == consent_data["consent_id"]
    assert get_consent_resp.json()["consent_hash"] == consent_data["consent_hash"]

    # 3. Rechazo si no se aceptan los términos
    rejected_terms = await async_client.post(
        "/api/v1/experience/consent",
        headers=auth_headers,
        json={
            "document_number": "1020304050",
            "otp_code": "839201",
            "terms_accepted": False,
        },
    )
    assert rejected_terms.status_code == 400

    # 4. Rechazo con OTP fallido/expirado simulado ('000000')
    rejected_otp = await async_client.post(
        "/api/v1/experience/consent",
        headers=auth_headers,
        json={
            "document_number": "1020304050",
            "otp_code": "000000",
            "terms_accepted": True,
        },
    )
    assert rejected_otp.status_code == 400

    # 5. Rechazo con formato de OTP no numérico (422)
    invalid_format = await async_client.post(
        "/api/v1/experience/consent",
        headers=auth_headers,
        json={
            "document_number": "1020304050",
            "otp_code": "abcdef",
            "terms_accepted": True,
        },
    )
    assert invalid_format.status_code == 422

    # 6. Consulta de consentimiento inexistente devuelve 404
    not_found_resp = await async_client.get(
        "/api/v1/experience/consent/9999999999",
        headers=auth_headers,
    )
    assert not_found_resp.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quote_edge_requiere_socio_y_cotiza(async_client: AsyncClient):
    """Valida canal quote-edge B2B: 401 si falta X-Partner-Id y cotización con la cabecera."""
    quote_payload = {
        "document_type": "CC",
        "document_number": "1020304050",
        "birth_date": "1990-05-15",
        "insured_amount": 100000000.0,
    }
    # Sin cabecera -> 401
    resp_no_header = await async_client.post("/api/v1/quote-edge/quotes", json=quote_payload)
    assert resp_no_header.status_code == 401

    # Con cabecera -> 200 (motor de tarifa de HU-WEB-03)
    resp_with_header = await async_client.post(
        "/api/v1/quote-edge/quotes",
        headers={"X-Partner-Id": "banco-aliado-1"},
        json=quote_payload,
    )
    assert resp_with_header.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hu_web_03_cotizacion_con_desglose_de_la_prima(async_client: AsyncClient, postgres_session):
    """HU-WEB-03: la cotización del canal web trae el aporte en pesos de cada factor."""
    from app.core.security import create_access_token

    advisor_token = create_access_token(subject="asesor@solventa.com", role="advisor")
    auth_headers = {"Authorization": f"Bearer {advisor_token}"}

    response = await async_client.post(
        "/api/v1/experience/quotes",
        headers=auth_headers,
        json={
            "document_type": "CC",
            "document_number": "1020304050",
            "birth_date": "1990-05-15",
            "insured_amount": 100000000.0,
            "occupation_risk": 2,
        },
    )

    assert response.status_code == 200
    tiers = response.json()["tiers"]
    assert len(tiers) == 3
    for tier in tiers:
        assert sum(factor["amount"] for factor in tier["breakdown"]) == tier["monthly_premium"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hu_web_04_cotizacion_degradada_por_timeout_del_buro(async_client: AsyncClient, postgres_session):
    """HU-WEB-04: si el buró supera los 400 ms, el canal web responde 200 con la cotización degradada."""
    from app.core.security import create_access_token

    advisor_token = create_access_token(subject="asesor@solventa.com", role="advisor")
    auth_headers = {"Authorization": f"Bearer {advisor_token}"}

    response = await async_client.post(
        "/api/v1/experience/quotes",
        headers=auth_headers,
        params={"simulated_delay": 0.45},
        json={
            "document_type": "CC",
            "document_number": "1020304050",
            "birth_date": "1990-05-15",
            "insured_amount": 100000000.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["degradation_reason"] == "TIMEOUT_EXCEEDED"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hu_web_05_la_cotizacion_queda_guardada_con_su_traza(async_client: AsyncClient, postgres_session):
    """HU-WEB-05 / HA-17: la cotización devuelta queda guardada tal cual, con la traza de su degradación."""
    from datetime import datetime
    from app.core.security import create_access_token
    from app.modules.rating.models import QuoteDB

    advisor_token = create_access_token(subject="asesor@solventa.com", role="advisor")
    response = await async_client.post(
        "/api/v1/experience/quotes",
        headers={"Authorization": f"Bearer {advisor_token}"},
        params={"simulated_delay": 0.45},
        json={
            "document_type": "CC",
            "document_number": "1020304050",
            "birth_date": "1990-05-15",
            "insured_amount": 100000000.0,
        },
    )

    quote = response.json()
    saved = await postgres_session.get(QuoteDB, quote["quote_id"])
    assert (saved.document_number, saved.status, saved.degradation_reason, saved.score_applied, saved.tiers) == (
        quote["document_number"], "degraded", "TIMEOUT_EXCEEDED", quote["score_applied"], quote["tiers"]
    )
    assert (saved.created_at, saved.expires_at) == (
        datetime.fromisoformat(quote["created_at"]), datetime.fromisoformat(quote["expires_at"])
    )
