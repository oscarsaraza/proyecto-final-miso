"""Cierre de sesión, huella vinculada al teléfono y recuperación de contraseña (TC-S1-12, TC-S1-10)."""
from datetime import timedelta

import pytest

from app.core.security import create_access_token
from app.modules.identity.service import (
    AccountLockedError,
    InvalidCredentialsError,
    InvalidTokenError,
    SamePasswordError,
    WeakPasswordError,
)
from tests.conftest import INSURED_EMAIL as EMAIL, INSURED_PASSWORD as PASSWORD

pytestmark = pytest.mark.integration


@pytest.fixture
async def tokens(identity, postgres_session):
    return await identity.login(postgres_session, EMAIL, PASSWORD, await identity.request_otp(postgres_session, EMAIL))


async def test_tc_s1_12_refresh_valido_emite_nuevos_tokens(identity, postgres_session, tokens):
    renewed = await identity.refresh(postgres_session, tokens.refresh_token)

    assert renewed.refresh_token != tokens.refresh_token


async def test_tc_s1_12_logout_revoca_el_refresh_token_y_es_repetible(identity, postgres_session, tokens):
    await identity.logout(postgres_session, tokens.refresh_token)
    await identity.logout(postgres_session, tokens.refresh_token)

    with pytest.raises(InvalidTokenError):
        await identity.refresh(postgres_session, tokens.refresh_token)


async def test_tc_s1_12_refresh_usado_no_se_puede_reutilizar(identity, postgres_session, tokens):
    await identity.refresh(postgres_session, tokens.refresh_token)

    with pytest.raises(InvalidTokenError):
        await identity.refresh(postgres_session, tokens.refresh_token)


async def test_tc_s1_12_access_token_y_token_alterado_no_sirven(identity, postgres_session, tokens):
    with pytest.raises(InvalidTokenError):
        await identity.logout(postgres_session, tokens.access_token)
    with pytest.raises(InvalidTokenError):
        await identity.refresh(postgres_session, tokens.refresh_token[:-2] + "xx")


async def test_tc_s1_12_refresh_de_usuario_inexistente_es_rechazado(identity, postgres_session):
    token = create_access_token(
        subject="ins-9999", role="insured", claims={"type": "refresh", "jti": "x"}, expires_delta=timedelta(days=1)
    )
    with pytest.raises(InvalidTokenError):
        await identity.refresh(postgres_session, token)


async def test_tc_s1_12_la_huella_sigue_activa_despues_de_cerrar_sesion(identity, postgres_session, tokens):
    device_id, secret = await identity.register_device(postgres_session, "ins-0001")
    await identity.logout(postgres_session, tokens.refresh_token)

    again = await identity.biometric_login(postgres_session, device_id, secret)

    assert again.full_name == "María Ruiz"


async def test_tc_s1_12_desactivar_huella_impide_entrar_con_ella(identity, postgres_session, tokens):
    device_id, secret = await identity.register_device(postgres_session, "ins-0001")
    await identity.revoke_device(postgres_session, "ins-0001", device_id)

    with pytest.raises(InvalidCredentialsError):
        await identity.biometric_login(postgres_session, device_id, secret)


async def test_tc_s1_12_secreto_de_dispositivo_equivocado_es_rechazado(identity, postgres_session, tokens):
    device_id, _ = await identity.register_device(postgres_session, "ins-0001")

    with pytest.raises(InvalidCredentialsError):
        await identity.biometric_login(postgres_session, device_id, "otro-secreto")
    with pytest.raises(InvalidCredentialsError):
        await identity.biometric_login(postgres_session, "no-existe", "x")


async def test_tc_s1_12_huella_respeta_el_bloqueo_de_la_cuenta(identity, postgres_session, clock, tokens):
    device_id, secret = await identity.register_device(postgres_session, "ins-0001")
    for _ in range(5):
        with pytest.raises((InvalidCredentialsError, AccountLockedError)):
            await identity.login(postgres_session, EMAIL, "otra-clave", "000000")

    with pytest.raises(AccountLockedError):
        await identity.biometric_login(postgres_session, device_id, secret)


async def test_recuperar_contrasena_desbloquea_cierra_sesiones_y_desvincula_huellas(
    identity, postgres_session, clock, sms, tokens
):
    device_id, secret = await identity.register_device(postgres_session, "ins-0001")
    clock.advance(timedelta(seconds=61))
    code = await identity.forgot_password(postgres_session, EMAIL)

    await identity.reset_password(postgres_session, EMAIL, code, "NuevaClave2026")

    assert "cambiar la contraseña" in sms.sent[-1][1]
    with pytest.raises(InvalidTokenError):
        await identity.refresh(postgres_session, tokens.refresh_token)
    with pytest.raises(InvalidCredentialsError):
        await identity.biometric_login(postgres_session, device_id, secret)
    clock.advance(timedelta(seconds=61))
    login_code = await identity.request_otp(postgres_session, EMAIL)
    assert (await identity.login(postgres_session, EMAIL, "NuevaClave2026", login_code)).access_token


async def test_recuperar_contrasena_exige_el_codigo_de_recuperacion(identity, postgres_session, clock):
    login_code = await identity.request_otp(postgres_session, EMAIL)

    with pytest.raises(InvalidCredentialsError):
        await identity.reset_password(postgres_session, EMAIL, login_code, "NuevaClave2026")


async def test_recuperar_contrasena_rechaza_claves_debiles(identity, postgres_session):
    code = await identity.forgot_password(postgres_session, EMAIL)

    with pytest.raises(WeakPasswordError):
        await identity.reset_password(postgres_session, EMAIL, code, "corta")


async def test_recuperar_contrasena_no_acepta_la_misma_y_conserva_el_codigo(identity, postgres_session):
    code = await identity.forgot_password(postgres_session, EMAIL)

    with pytest.raises(SamePasswordError):
        await identity.reset_password(postgres_session, EMAIL, code, PASSWORD)
    await identity.reset_password(postgres_session, EMAIL, code, "NuevaClave2026")


async def test_recuperar_contrasena_con_codigo_malo_no_dice_si_la_clave_es_la_misma(identity, postgres_session):
    await identity.forgot_password(postgres_session, EMAIL)

    with pytest.raises(InvalidCredentialsError):
        await identity.reset_password(postgres_session, EMAIL, "000000", PASSWORD)
