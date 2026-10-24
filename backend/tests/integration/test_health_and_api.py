"""Pruebas de integración del arnés técnico base: Health check (ALB), Root y Placeholders 501."""
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


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
async def test_hu_web_02_validacion_asegurabilidad_cliente(async_client: AsyncClient):
    """HU-WEB-02 / TC-S1-03: validación de asegurabilidad sociodemográfica de clientes por edad."""
    from app.core.security import create_access_token
    advisor_token = create_access_token(subject="asesor@solventa.com", role="advisor")
    auth_headers = {"Authorization": f"Bearer {advisor_token}"}

    # 1. Cliente en rango asegurable (ej. 36 años) -> 200 ELIGIBLE
    eligible_payload = {
        "document_type": "CC",
        "document_number": "1020304050",
        "first_name": "Carlos",
        "last_name": "Perez",
        "birth_date": "1990-05-15",
        "email": "carlos@test.com",
        "phone": "3001234567",
    }
    resp_ok = await async_client.post(
        "/api/v1/experience/clients/validate",
        headers=auth_headers,
        json=eligible_payload,
    )
    assert resp_ok.status_code == 200
    data = resp_ok.json()
    assert data["status"] == "ELIGIBLE"
    assert data["age"] >= 18 and data["age"] <= 75

    # 2. Cliente menor de edad (ej. 11 años) -> 400 Bad Request
    minor_payload = {**eligible_payload, "birth_date": "2015-01-01"}
    resp_minor = await async_client.post(
        "/api/v1/experience/clients/validate",
        headers=auth_headers,
        json=minor_payload,
    )
    assert resp_minor.status_code == 400
    assert "Debe tener entre 18 y 75 años para ser asegurable" in resp_minor.json()["detail"]

    # 3. Cliente mayor a 75 años (ej. 86 años) -> 400 Bad Request
    senior_payload = {**eligible_payload, "birth_date": "1940-01-01"}
    resp_senior = await async_client.post(
        "/api/v1/experience/clients/validate",
        headers=auth_headers,
        json=senior_payload,
    )
    assert resp_senior.status_code == 400
    assert "Debe tener entre 18 y 75 años para ser asegurable" in resp_senior.json()["detail"]

    # 4. Formato de fecha inválido -> 422 Unprocessable Entity
    invalid_payload = {**eligible_payload, "birth_date": "fecha-invalida"}
    resp_invalid = await async_client.post(
        "/api/v1/experience/clients/validate",
        headers=auth_headers,
        json=invalid_payload,
    )
    assert resp_invalid.status_code == 422


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
    """Valida canal quote-edge B2B: 401 si falta token Bearer de socio y cotización 200 con token válido (HU-WEB-10)."""
    from app.core.security import create_partner_access_token

    quote_payload = {
        "document_type": "CC",
        "document_number": "1020304050",
        "birth_date": "1990-05-15",
        "insured_amount": 100000000.0,
    }
    # Sin token Bearer -> 401
    resp_no_header = await async_client.post("/api/v1/quote-edge/quotes", json=quote_payload)
    assert resp_no_header.status_code == 401

    # Con token Bearer de socio activo -> 200 (motor de tarifa de HU-WEB-03 y confinamiento HU-WEB-10)
    partner_token = create_partner_access_token(client_id="banco_aliado", partner_id="banco-aliado-1")
    resp_with_token = await async_client.post(
        "/api/v1/quote-edge/quotes",
        headers={"Authorization": f"Bearer {partner_token}"},
        json=quote_payload,
    )
    assert resp_with_token.status_code == 200
    assert resp_with_token.json()["partner_id"] == "banco-aliado-1"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tc_06_canal_de_socios_desactivado(async_client: AsyncClient):
    """El canal quote-edge rechaza peticiones sin autenticación o con cabecera obsoleta X-Partner-Id (HOTFIX-configuracion-de-produccion / HU-WEB-10)."""
    quote_payload = {
        "document_type": "CC",
        "document_number": "1020304050",
        "birth_date": "1990-05-15",
        "insured_amount": 100000000.0,
    }
    for headers in ({}, {"X-Partner-Id": "banco-aliado-1"}):
        response = await async_client.post("/api/v1/quote-edge/quotes", headers=headers, json=quote_payload)
        assert response.status_code in (401, 404)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tc_09_token_firmado_con_otra_llave_es_rechazado(async_client: AsyncClient):
    """Un token firmado con otra llave, como la publicada antes, recibe 401 (HOTFIX-configuracion-de-produccion)."""
    ahora = datetime.now(timezone.utc)
    claims = {"sub": "asesor@example.com", "role": "advisor", "type": "access", "iat": ahora, "exp": ahora + timedelta(minutes=5)}
    falso = jwt.encode(claims, secrets.token_urlsafe(48), algorithm="HS256")
    valido = create_access_token(subject="asesor@example.com", role="advisor")
    cuerpo = {"birth_date": "1990-05-15"}

    rechazado = await async_client.post("/api/v1/experience/clients/validate", json=cuerpo, headers={"Authorization": f"Bearer {falso}"})
    aceptado = await async_client.post("/api/v1/experience/clients/validate", json=cuerpo, headers={"Authorization": f"Bearer {valido}"})

    assert rechazado.status_code == 401
    assert aceptado.status_code != 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tc_07_cors_no_autoriza_origenes_ajenos(async_client: AsyncClient):
    """Sin CORS_ORIGINS ningún origen ajeno recibe permiso (HOTFIX-configuracion-de-produccion)."""
    ajeno = {"Origin": "https://ajeno.example"}
    preflight = await async_client.options(
        "/api/v1/experience/auth/login", headers={**ajeno, "Access-Control-Request-Method": "POST"}
    )
    simple = await async_client.get("/health", headers=ajeno)

    assert "access-control-allow-origin" not in preflight.headers
    assert "access-control-allow-origin" not in simple.headers
    assert "access-control-allow-credentials" not in simple.headers


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
