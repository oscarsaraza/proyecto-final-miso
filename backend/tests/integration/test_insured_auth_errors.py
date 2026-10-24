"""Respuestas de error del BFF del asegurado (TC-S1-10, TC-S1-12)."""
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.modules.identity.service import (
    AccountLockedError,
    InvalidCredentialsError,
    InvalidTokenError,
    RateLimitedError,
    SamePasswordError,
    SmsUnavailableError,
    WeakPasswordError,
    insured_auth_service,
)

pytestmark = pytest.mark.integration

LOCKED_UNTIL = datetime(2026, 10, 9, 12, 15, tzinfo=timezone.utc)


def raising(error: Exception):
    async def fake(*args, **kwargs):
        raise error

    return fake


def access_token(user_id: str = "ins-0001") -> dict:
    token = create_access_token(subject=user_id, role="insured", claims={"type": "access"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "error, status",
    [(RateLimitedError(42), 429), (SmsUnavailableError(), 503)],
)
@pytest.mark.parametrize("path, method", [("/api/v1/auth/otp", "request_otp"), ("/api/v1/auth/password/forgot", "forgot_password")])
async def test_pedir_codigo_informa_limite_y_falla_del_sms(
    async_client: AsyncClient, monkeypatch, error, status, path, method
):
    monkeypatch.setattr(insured_auth_service, method, raising(error))

    response = await async_client.post(path, json={"email": "maria.ruiz@correo.co"})

    assert response.status_code == status
    if status == 429:
        assert response.headers["Retry-After"] == "42"


@pytest.mark.parametrize("path, method, body", [
    ("/api/v1/auth/login", "login", {"email": "a@b.co", "password": "x", "otp_code": "123456"}),
    ("/api/v1/auth/biometric", "biometric_login", {"device_id": "d", "device_secret": "s"}),
])
async def test_ingreso_suspendido_responde_423_con_tiempo_restante(async_client: AsyncClient, monkeypatch, path, method, body):
    monkeypatch.setattr(insured_auth_service, method, raising(AccountLockedError(LOCKED_UNTIL, 900)))

    response = await async_client.post(path, json=body)

    assert response.status_code == 423
    assert response.headers["Retry-After"] == "900"
    assert response.json()["detail"] == "Por seguridad, el ingreso está suspendido temporalmente."


@pytest.mark.parametrize("path, method, body", [
    ("/api/v1/auth/login", "login", {"email": "a@b.co", "password": "x", "otp_code": "123456"}),
    ("/api/v1/auth/biometric", "biometric_login", {"device_id": "d", "device_secret": "s"}),
    ("/api/v1/auth/password/reset", "reset_password", {"email": "a@b.co", "code": "123456", "new_password": "Clave2026x"}),
])
async def test_limite_por_ip_responde_429(async_client: AsyncClient, monkeypatch, path, method, body):
    monkeypatch.setattr(insured_auth_service, method, raising(RateLimitedError(30)))

    response = await async_client.post(path, json=body)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "30"


async def test_huella_invalida_responde_401(async_client: AsyncClient, monkeypatch):
    monkeypatch.setattr(insured_auth_service, "biometric_login", raising(InvalidCredentialsError()))

    response = await async_client.post("/api/v1/auth/biometric", json={"device_id": "d", "device_secret": "s"})

    assert response.status_code == 401


@pytest.mark.parametrize("error, status", [
    (WeakPasswordError(), 422),
    (InvalidCredentialsError(), 401),
    (SamePasswordError(), 409),
])
async def test_recuperar_contrasena_responde_cada_error(async_client: AsyncClient, monkeypatch, error, status):
    monkeypatch.setattr(insured_auth_service, "reset_password", raising(error))

    response = await async_client.post(
        "/api/v1/auth/password/reset", json={"email": "a@b.co", "code": "123456", "new_password": "Clave2026x"}
    )

    assert response.status_code == status


async def test_refresh_con_token_revocado_responde_401(async_client: AsyncClient, monkeypatch):
    monkeypatch.setattr(insured_auth_service, "refresh", raising(InvalidTokenError()))

    response = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": "x"})

    assert response.status_code == 401


async def test_registrar_dispositivo_de_cuenta_inexistente_responde_401(async_client: AsyncClient, monkeypatch):
    monkeypatch.setattr(insured_auth_service, "register_device", raising(InvalidTokenError()))

    response = await async_client.post("/api/v1/auth/devices", headers=access_token("ins-9999"))

    assert response.status_code == 401


@pytest.mark.usefixtures("seeded_insured")
async def test_desactivar_huella_con_access_token_responde_204(async_client: AsyncClient):
    response = await async_client.delete("/api/v1/auth/devices/no-existe", headers=access_token())

    assert response.status_code == 204
