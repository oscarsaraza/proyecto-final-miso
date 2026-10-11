"""Pruebas de cierre de sesión y revocación del refresh token (TC-S1-12)."""
from datetime import timedelta

import pytest

from app.core.security import create_access_token, decode_access_token, get_password_hash
from app.modules.identity.service import (
    InsuredAccount,
    InsuredAuthService,
    InvalidTokenError,
)

EMAIL = "maria.ruiz@correo.co"
PASSWORD = "Solventa2026!"


@pytest.fixture
def service():
    svc = InsuredAuthService()
    svc.register(
        InsuredAccount(
            user_id="ins-0001",
            email=EMAIL,
            full_name="María Ruiz",
            document_number="1020304050",
            password_hash=get_password_hash(PASSWORD),
        )
    )
    return svc


@pytest.fixture
def tokens(service):
    return service.login(EMAIL, PASSWORD, service.request_otp(EMAIL))


@pytest.mark.unit
def test_tc_s1_12_refresh_valido_emite_nuevos_tokens(service, tokens):
    renewed = service.refresh(tokens.refresh_token)

    assert renewed.refresh_token != tokens.refresh_token
    assert decode_access_token(renewed.access_token)["sub"] == "ins-0001"


@pytest.mark.unit
def test_tc_s1_12_logout_revoca_el_refresh_token(service, tokens):
    service.logout(tokens.refresh_token)

    with pytest.raises(InvalidTokenError):
        service.refresh(tokens.refresh_token)


@pytest.mark.unit
def test_tc_s1_12_logout_repetido_no_falla(service, tokens):
    service.logout(tokens.refresh_token)
    service.logout(tokens.refresh_token)


@pytest.mark.unit
def test_tc_s1_12_refresh_usado_no_se_puede_reutilizar(service, tokens):
    service.refresh(tokens.refresh_token)

    with pytest.raises(InvalidTokenError):
        service.refresh(tokens.refresh_token)


@pytest.mark.unit
def test_tc_s1_12_access_token_no_sirve_para_logout(service, tokens):
    with pytest.raises(InvalidTokenError):
        service.logout(tokens.access_token)


@pytest.mark.unit
def test_tc_s1_12_token_alterado_es_rechazado(service, tokens):
    with pytest.raises(InvalidTokenError):
        service.logout(tokens.refresh_token[:-2] + "xx")


@pytest.mark.unit
def test_tc_s1_12_refresh_de_usuario_inexistente_es_rechazado(service):
    orphan = create_access_token(
        subject="ins-9999",
        role="insured",
        claims={"type": "refresh", "jti": "abc123"},
        expires_delta=timedelta(minutes=5),
    )

    with pytest.raises(InvalidTokenError):
        service.refresh(orphan)
