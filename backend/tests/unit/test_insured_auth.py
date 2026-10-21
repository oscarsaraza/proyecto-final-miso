"""Acceso alternativo del asegurado con contraseña y código por SMS sobre PostgreSQL (TC-S1-10)."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.security import decode_access_token
from app.modules.identity.db_models import LoginAttemptDB
from app.modules.identity.service import (
    OTP_TTL,
    AccountLockedError,
    InvalidCredentialsError,
    RateLimitedError,
    SmsUnavailableError,
)
from tests.conftest import INSURED_EMAIL as EMAIL, INSURED_PASSWORD as PASSWORD, INSURED_PHONE

pytestmark = pytest.mark.integration


def wrong(code: str) -> str:
    return f"{(int(code) + 1) % 1_000_000:06d}"


async def fail_password(identity, db, times: int):
    for _ in range(times):
        with pytest.raises((InvalidCredentialsError, AccountLockedError)):
            await identity.login(db, EMAIL, "otra-clave", "000000")


async def test_tc_s1_10_login_exitoso_emite_tokens_del_asegurado(identity, postgres_session, sms):
    code = await identity.request_otp(postgres_session, EMAIL)

    tokens = await identity.login(postgres_session, EMAIL, PASSWORD, code)

    claims = decode_access_token(tokens.access_token)
    assert claims["sub"] == "ins-0001" and claims["role"] == "insured" and claims["type"] == "access"
    assert tokens.full_name == "María Ruiz"
    assert sms.sent[0][0] == INSURED_PHONE and code in sms.sent[0][1]


async def test_tc_s1_10_correo_sin_distinguir_mayusculas(identity, postgres_session):
    code = await identity.request_otp(postgres_session, "MARIA.Ruiz@correo.co")

    assert (await identity.login(postgres_session, " Maria.Ruiz@Correo.co ", PASSWORD, code)).access_token


async def test_tc_s1_10_correo_desconocido_no_envia_sms_ni_entra(identity, postgres_session, sms):
    assert await identity.request_otp(postgres_session, "nadie@correo.co") is None
    assert sms.sent == []
    with pytest.raises(InvalidCredentialsError):
        await identity.login(postgres_session, "nadie@correo.co", PASSWORD, "123456")


async def test_tc_s1_10_codigo_es_de_un_solo_uso_y_vence(identity, postgres_session, clock):
    code = await identity.request_otp(postgres_session, EMAIL)
    await identity.login(postgres_session, EMAIL, PASSWORD, code)
    with pytest.raises(InvalidCredentialsError):
        await identity.login(postgres_session, EMAIL, PASSWORD, code)

    clock.advance(timedelta(seconds=61))
    code = await identity.request_otp(postgres_session, EMAIL)
    clock.advance(OTP_TTL + timedelta(seconds=1))
    with pytest.raises(InvalidCredentialsError):
        await identity.login(postgres_session, EMAIL, PASSWORD, code)


async def test_tc_s1_10_pedir_codigo_nuevo_invalida_el_anterior(identity, postgres_session, clock):
    first = await identity.request_otp(postgres_session, EMAIL)
    clock.advance(timedelta(seconds=61))
    second = await identity.request_otp(postgres_session, EMAIL)

    if first != second:
        with pytest.raises(InvalidCredentialsError):
            await identity.login(postgres_session, EMAIL, PASSWORD, first)
    assert (await identity.login(postgres_session, EMAIL, PASSWORD, second)).access_token


async def test_tc_s1_10_tres_codigos_equivocados_descartan_el_codigo(identity, postgres_session):
    code = await identity.request_otp(postgres_session, EMAIL)

    for _ in range(3):
        with pytest.raises(InvalidCredentialsError):
            await identity.login(postgres_session, EMAIL, PASSWORD, wrong(code))

    with pytest.raises(InvalidCredentialsError):
        await identity.login(postgres_session, EMAIL, PASSWORD, code)


async def test_tc_s1_10_codigos_y_contrasenas_equivocados_suman_al_bloqueo(identity, postgres_session):
    code = await identity.request_otp(postgres_session, EMAIL)
    for _ in range(3):
        with pytest.raises(InvalidCredentialsError):
            await identity.login(postgres_session, EMAIL, PASSWORD, wrong(code))
    with pytest.raises(InvalidCredentialsError):
        await identity.login(postgres_session, EMAIL, "otra-clave", "000000")

    with pytest.raises(AccountLockedError):
        await identity.login(postgres_session, EMAIL, "otra-clave", "000000")


async def test_tc_s1_10_correo_inexistente_se_bloquea_igual_para_no_revelar_cuentas(identity, postgres_session):
    for _ in range(4):
        with pytest.raises(InvalidCredentialsError):
            await identity.login(postgres_session, "nadie@correo.co", "x", "000000")

    with pytest.raises(AccountLockedError) as locked:
        await identity.login(postgres_session, "nadie@correo.co", "x", "000000")
    assert locked.value.retry_after == 15 * 60


async def test_tc_s1_10_limite_de_codigos_aplica_igual_a_correos_inexistentes(identity, postgres_session):
    assert await identity.request_otp(postgres_session, "nadie@correo.co") is None

    with pytest.raises(RateLimitedError):
        await identity.request_otp(postgres_session, "nadie@correo.co")


async def test_tc_s1_10_ingreso_exitoso_reinicia_el_limite_de_codigos(identity, postgres_session, clock):
    for _ in range(4):
        await identity.request_otp(postgres_session, EMAIL)
        clock.advance(timedelta(seconds=61))
    code = await identity.request_otp(postgres_session, EMAIL)
    await identity.login(postgres_session, EMAIL, PASSWORD, code)

    assert await identity.request_otp(postgres_session, EMAIL)


async def test_tc_s1_10_bloquea_al_quinto_intento_con_contrasena_equivocada(identity, postgres_session, clock):
    await fail_password(identity, postgres_session, 4)

    code = await identity.request_otp(postgres_session, EMAIL)
    with pytest.raises(AccountLockedError) as locked:
        await identity.login(postgres_session, EMAIL, "otra-clave", code)

    assert locked.value.locked_until == clock.now + timedelta(minutes=15)
    assert locked.value.retry_after == 15 * 60


async def test_tc_s1_10_cuenta_bloqueada_rechaza_aun_con_credenciales_correctas(identity, postgres_session, clock):
    await fail_password(identity, postgres_session, 5)
    clock.advance(timedelta(minutes=1))

    with pytest.raises(AccountLockedError):
        await identity.login(postgres_session, EMAIL, PASSWORD, "123456")


async def test_tc_s1_10_bloqueo_expira_y_el_ingreso_exitoso_reinicia_el_conteo(identity, postgres_session, clock):
    await fail_password(identity, postgres_session, 5)
    clock.advance(timedelta(minutes=15))

    code = await identity.request_otp(postgres_session, EMAIL)
    assert (await identity.login(postgres_session, EMAIL, PASSWORD, code)).access_token

    await fail_password(identity, postgres_session, 5)
    clock.advance(timedelta(minutes=1))
    with pytest.raises(AccountLockedError) as locked:
        await identity.login(postgres_session, EMAIL, PASSWORD, "000000")
    assert locked.value.retry_after == 14 * 60


async def test_tc_s1_10_bloqueos_seguidos_crecen_a_30_minutos(identity, postgres_session, clock):
    await fail_password(identity, postgres_session, 5)
    clock.advance(timedelta(minutes=15))
    await fail_password(identity, postgres_session, 4)

    with pytest.raises(AccountLockedError) as locked:
        await identity.login(postgres_session, EMAIL, "otra-clave", "000000")

    assert locked.value.retry_after == 30 * 60


async def test_tc_s1_10_pedir_codigo_antes_de_un_minuto_responde_429(identity, postgres_session, clock):
    await identity.request_otp(postgres_session, EMAIL)
    clock.advance(timedelta(seconds=10))

    with pytest.raises(RateLimitedError) as limited:
        await identity.request_otp(postgres_session, EMAIL)
    assert limited.value.retry_after == 50


async def test_tc_s1_10_limite_por_ip_frena_ataques_a_muchos_correos(identity, postgres_session):
    for i in range(20):
        with pytest.raises(InvalidCredentialsError):
            await identity.login(postgres_session, f"victima{i}@correo.co", "x", "123456", ip="9.9.9.9")

    with pytest.raises(RateLimitedError):
        await identity.login(postgres_session, EMAIL, PASSWORD, "123456", ip="9.9.9.9")
    code = await identity.request_otp(postgres_session, EMAIL, ip="8.8.8.8")
    assert (await identity.login(postgres_session, EMAIL, PASSWORD, code, ip="8.8.8.8")).access_token


async def test_tc_s1_10_falla_del_sms_no_deja_codigo_guardado(identity, postgres_session, sms, clock):
    sms.fail = True
    with pytest.raises(SmsUnavailableError):
        await identity.request_otp(postgres_session, EMAIL)

    sms.fail = False
    code = await identity.request_otp(postgres_session, EMAIL)
    assert (await identity.login(postgres_session, EMAIL, PASSWORD, code)).access_token


async def test_tc_s1_10_cada_intento_queda_en_la_auditoria(identity, postgres_session):
    code = await identity.request_otp(postgres_session, EMAIL, ip="1.2.3.4")
    with pytest.raises(InvalidCredentialsError):
        await identity.login(postgres_session, EMAIL, "otra-clave", code, ip="1.2.3.4")
    await identity.login(postgres_session, EMAIL, PASSWORD, code, ip="1.2.3.4")

    rows = (await postgres_session.execute(select(LoginAttemptDB).order_by(LoginAttemptDB.id))).scalars().all()
    assert [(r.channel, r.result, r.ip) for r in rows] == [
        ("otp_request", "success", "1.2.3.4"),
        ("password", "bad_password", "1.2.3.4"),
        ("password", "success", "1.2.3.4"),
    ]
