"""Pruebas unitarias de autenticación OAuth2 de socios B2B, auditoría JSON y confinamiento (HU-WEB-10)."""
from datetime import timedelta
import json
import logging
import pytest
from fastapi import HTTPException
from starlette.requests import Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import (
    authenticate_partner,
    create_access_token,
    create_partner_access_token,
    create_refresh_token,
    decode_access_token,
    get_current_partner,
)
from app.modules.rating.models import PartnerStatus, QuoteRequest
from app.modules.rating.service import rating_service


def _dummy_request(path: str = "/api/v1/quote-edge/quotes") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": [],
        "query_string": b"",
    }
    return Request(scope)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_seed_default_partners_is_idempotent(test_db_session):
    """Verifica que los socios semilla (activo y revocado) se creen de forma idempotente."""
    partners_first = await rating_service.seed_default_partners(test_db_session)
    partners_second = await rating_service.seed_default_partners(test_db_session)

    assert len(partners_first) == 2
    assert len(partners_second) == 2

    active_partner = test_db_session.partners_by_client_id["banco_aliado"]
    revoked_partner = test_db_session.partners_by_client_id["socio_inactivo"]

    assert active_partner.partner_id == "banco-aliado-1"
    assert active_partner.status == PartnerStatus.ACTIVE.value
    assert active_partner.quota_limit == 50000
    assert active_partner.quota_used == 0

    assert revoked_partner.partner_id == "socio-inactivo-1"
    assert revoked_partner.status == PartnerStatus.REVOKED.value


@pytest.mark.unit
def test_create_partner_access_token_claims():
    """Verifica que el JWT emitido para un socio incluya sub, partner_id y role='partner'."""
    token = create_partner_access_token(
        client_id="banco_aliado",
        partner_id="banco-aliado-1",
    )
    payload = decode_access_token(token)
    assert payload["sub"] == "banco_aliado"
    assert payload["partner_id"] == "banco-aliado-1"
    assert payload["role"] == "partner"
    assert payload["type"] == "access"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_authenticate_partner_success(test_db_session):
    """Verifica autenticación exitosa de socio activo con bcrypt."""
    partner = await authenticate_partner(
        session=test_db_session,
        client_id="banco_aliado",
        client_secret="AliadoSecret2026*",
    )
    assert partner.partner_id == "banco-aliado-1"
    assert partner.status == PartnerStatus.ACTIVE.value


@pytest.mark.unit
@pytest.mark.asyncio
async def test_authenticate_partner_invalid_credentials_logs_security_event(test_db_session, caplog):
    """Verifica rechazo HTTP 401 y log PARTNER_AUTH_FAILED ante credenciales erróneas."""
    with caplog.at_level(logging.WARNING, logger="solventa.security.partner"):
        with pytest.raises(HTTPException) as exc_info:
            await authenticate_partner(
                session=test_db_session,
                client_id="banco_aliado",
                client_secret="ClaveIncorrecta*",
            )

    assert exc_info.value.status_code == 401
    assert len(caplog.records) == 1
    log_data = json.loads(caplog.records[0].message)
    assert log_data["event"] == "partner_security_audit"
    assert log_data["event_code"] == "PARTNER_AUTH_FAILED"
    assert log_data["client_id"] == "banco_aliado"
    assert log_data["partner_id"] == "banco-aliado-1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_authenticate_partner_revoked_logs_security_event(test_db_session, caplog):
    """Verifica rechazo HTTP 401 y log PARTNER_REVOKED para socio revocado."""
    with caplog.at_level(logging.WARNING, logger="solventa.security.partner"):
        with pytest.raises(HTTPException) as exc_info:
            await authenticate_partner(
                session=test_db_session,
                client_id="socio_inactivo",
                client_secret="Inactivo2026*",
            )

    assert exc_info.value.status_code == 401
    assert len(caplog.records) == 1
    log_data = json.loads(caplog.records[0].message)
    assert log_data["event_code"] == "PARTNER_REVOKED"
    assert log_data["client_id"] == "socio_inactivo"
    assert log_data["partner_id"] == "socio-inactivo-1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_partner_rejects_advisor_and_refresh_tokens(test_db_session, caplog):
    """Verifica que tokens de otros roles (advisor) o de tipo refresh sean rechazados con PARTNER_ROLE_MISMATCH."""
    advisor_token = create_access_token(subject="asesor@solventa.com", role="advisor")
    refresh_token = create_refresh_token(subject="banco_aliado", role="partner")

    with caplog.at_level(logging.WARNING, logger="solventa.security.partner"):
        for token in (advisor_token, refresh_token):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_partner(
                    request=_dummy_request(),
                    credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
                    session=test_db_session,
                )
            assert exc_info.value.status_code == 401

    assert len(caplog.records) == 2
    for record in caplog.records:
        assert json.loads(record.message)["event_code"] == "PARTNER_ROLE_MISMATCH"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_partner_rejects_deleted_or_expired_partner(test_db_session, caplog):
    """Verifica rechazo ante socio inexistente en BD o token expirado."""
    ghost_token = create_partner_access_token(client_id="fantasma", partner_id="socio-fantasma-99")
    expired_token = create_partner_access_token(
        client_id="banco_aliado",
        partner_id="banco-aliado-1",
        expires_delta=timedelta(seconds=-5),
    )

    with caplog.at_level(logging.WARNING, logger="solventa.security.partner"):
        with pytest.raises(HTTPException) as exc_ghost:
            await get_current_partner(
                request=_dummy_request(),
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=ghost_token),
                session=test_db_session,
            )
        with pytest.raises(HTTPException) as exc_exp:
            await get_current_partner(
                request=_dummy_request(),
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token),
                session=test_db_session,
            )

    assert exc_ghost.value.status_code == 401
    assert exc_exp.value.status_code == 401
    codes = [json.loads(r.message)["event_code"] for r in caplog.records]
    assert codes == ["PARTNER_AUTH_FAILED", "PARTNER_TOKEN_EXPIRED"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_partner_quote_increments_quota_and_isolates_partner_records(test_db_session):
    """Verifica incremento de quota_used y confinamiento por partner_id en RatingService."""
    req = QuoteRequest(
        document_type="CC",
        document_number="1020304050",
        birth_date="1990-05-15",
        insured_amount=120000000.0,
    )
    quote = await rating_service.create_quote(
        session=test_db_session,
        request=req,
        partner_id="banco-aliado-1",
    )

    partner = test_db_session.partners_by_id["banco-aliado-1"]
    assert partner.quota_used == 1

    # Consulta por el socio propietario -> retorna la cotización
    own_quote = await rating_service.get_partner_quote(
        session=test_db_session,
        quote_id=quote.quote_id,
        partner_id="banco-aliado-1",
    )
    assert own_quote is not None
    assert own_quote.partner_id == "banco-aliado-1"

    # Consulta por otro socio -> retorna None
    other_quote = await rating_service.get_partner_quote(
        session=test_db_session,
        quote_id=quote.quote_id,
        partner_id="otro-socio-2",
    )
    assert other_quote is None
