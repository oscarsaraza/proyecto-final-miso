"""Pruebas de acceso alternativo del asegurado con contraseña y segundo factor (TC-S1-10)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import decode_access_token, get_password_hash
from app.modules.identity.service import (
    LOCKOUT_DURATION,
    OTP_TTL,
    AccountLockedError,
    InsuredAccount,
    InsuredAuthService,
    InvalidCredentialsError,
)

EMAIL = "maria.ruiz@correo.co"
PASSWORD = "Solventa2026!"
PASSWORD_HASH = get_password_hash(PASSWORD)


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, delta: timedelta):
        self.now += delta


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def service(clock):
    svc = InsuredAuthService(clock=clock)
    svc.register(
        InsuredAccount(
            user_id="ins-0001",
            email=EMAIL,
            full_name="María Ruiz",
            document_number="1020304050",
            password_hash=PASSWORD_HASH,
        )
    )
    return svc


def wrong_code(code: str) -> str:
    return f"{(int(code) + 1) % 1_000_000:06d}"


@pytest.mark.unit
def test_tc_s1_10_login_exitoso_emite_tokens_del_asegurado(service):
    code = service.request_otp(EMAIL)

    tokens = service.login(EMAIL, PASSWORD, code)

    access = decode_access_token(tokens.access_token)
    refresh = decode_access_token(tokens.refresh_token)
    assert access["sub"] == "ins-0001"
    assert access["role"] == "insured"
    assert access["type"] == "access"
    assert refresh["type"] == "refresh"
    assert refresh["jti"]
    assert tokens.full_name == "María Ruiz"


@pytest.mark.unit
def test_tc_s1_10_correo_sin_distinguir_mayusculas(service):
    code = service.request_otp("Maria.Ruiz@Correo.co")

    assert service.login("MARIA.RUIZ@correo.co", PASSWORD, code).access_token


@pytest.mark.unit
def test_tc_s1_10_otp_tiene_seis_digitos(service):
    code = service.request_otp(EMAIL)

    assert len(code) == 6 and code.isdigit()


@pytest.mark.unit
def test_tc_s1_10_correo_desconocido_no_genera_codigo_ni_entra(service):
    assert service.request_otp("nadie@correo.co") is None
    with pytest.raises(InvalidCredentialsError):
        service.login("nadie@correo.co", PASSWORD, "123456")


@pytest.mark.unit
def test_tc_s1_10_contrasena_incorrecta_rechaza(service):
    code = service.request_otp(EMAIL)

    with pytest.raises(InvalidCredentialsError):
        service.login(EMAIL, "otra-clave", code)


@pytest.mark.unit
def test_tc_s1_10_codigo_incorrecto_rechaza(service):
    code = service.request_otp(EMAIL)

    with pytest.raises(InvalidCredentialsError):
        service.login(EMAIL, PASSWORD, wrong_code(code))


@pytest.mark.unit
def test_tc_s1_10_codigo_es_de_un_solo_uso(service):
    code = service.request_otp(EMAIL)
    service.login(EMAIL, PASSWORD, code)

    with pytest.raises(InvalidCredentialsError):
        service.login(EMAIL, PASSWORD, code)


@pytest.mark.unit
def test_tc_s1_10_codigo_vencido_rechaza(service, clock):
    code = service.request_otp(EMAIL)
    clock.advance(OTP_TTL + timedelta(seconds=1))

    with pytest.raises(InvalidCredentialsError):
        service.login(EMAIL, PASSWORD, code)


@pytest.mark.unit
def test_tc_s1_10_bloquea_al_tercer_intento_fallido(service):
    code = service.request_otp(EMAIL)
    for _ in range(2):
        with pytest.raises(InvalidCredentialsError):
            service.login(EMAIL, "otra-clave", code)

    with pytest.raises(AccountLockedError):
        service.login(EMAIL, "otra-clave", code)


@pytest.mark.unit
def test_tc_s1_10_cuenta_bloqueada_rechaza_aun_con_credenciales_correctas(service):
    code = service.request_otp(EMAIL)
    for _ in range(3):
        with pytest.raises((InvalidCredentialsError, AccountLockedError)):
            service.login(EMAIL, "otra-clave", code)

    with pytest.raises(AccountLockedError):
        service.login(EMAIL, PASSWORD, code)


@pytest.mark.unit
def test_tc_s1_10_bloqueo_expira_a_los_15_minutos(service, clock):
    code = service.request_otp(EMAIL)
    for _ in range(3):
        with pytest.raises((InvalidCredentialsError, AccountLockedError)):
            service.login(EMAIL, "otra-clave", code)

    clock.advance(LOCKOUT_DURATION)
    new_code = service.request_otp(EMAIL)

    assert service.login(EMAIL, PASSWORD, new_code).access_token


@pytest.mark.unit
def test_tc_s1_10_login_exitoso_reinicia_intentos_fallidos(service):
    code = service.request_otp(EMAIL)
    for _ in range(2):
        with pytest.raises(InvalidCredentialsError):
            service.login(EMAIL, "otra-clave", code)
    service.login(EMAIL, PASSWORD, code)

    new_code = service.request_otp(EMAIL)
    for _ in range(2):
        with pytest.raises(InvalidCredentialsError):
            service.login(EMAIL, "otra-clave", new_code)
