"""Pruebas de integración para endpoints BFF de autenticación y autorización RBAC (HU-WEB-13.2)."""
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token, generate_totp
from app.modules.auth.service import (
    DEFAULT_SEED_NAME,
    DEFAULT_SEED_PASSWORD,
    DEFAULT_SEED_TOTP_SECRET,
    DEFAULT_SEED_USERNAME,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """Valida inicio de sesión exitoso retornando JWT con rol advisor y nombre de asesor (Criterio 1)."""
    valid_totp = generate_totp(DEFAULT_SEED_TOTP_SECRET)
    response = await async_client.post(
        "/api/v1/experience/auth/login",
        json={
            "username": DEFAULT_SEED_USERNAME,
            "password": DEFAULT_SEED_PASSWORD,
            "totp_code": valid_totp,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "advisor"
    assert data["advisor_name"] == DEFAULT_SEED_NAME
    assert data["expires_in"] == 900


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_401(async_client: AsyncClient):
    """Valida rechazo unificado HTTP 401 ante contraseña o TOTP inválidos (Criterio 2)."""
    valid_totp = generate_totp(DEFAULT_SEED_TOTP_SECRET)

    # 1. Contraseña errónea
    resp_bad_pass = await async_client.post(
        "/api/v1/experience/auth/login",
        json={
            "username": DEFAULT_SEED_USERNAME,
            "password": "PasswordIncorrecto123*",
            "totp_code": valid_totp,
        },
    )
    assert resp_bad_pass.status_code == 401
    assert resp_bad_pass.json()["detail"] == "Credenciales o código de verificación inválidos"

    # 2. Código TOTP erróneo
    resp_bad_totp = await async_client.post(
        "/api/v1/experience/auth/login",
        json={
            "username": DEFAULT_SEED_USERNAME,
            "password": DEFAULT_SEED_PASSWORD,
            "totp_code": "000000",
        },
    )
    assert resp_bad_totp.status_code == 401
    assert resp_bad_totp.json()["detail"] == "Credenciales o código de verificación inválidos"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_lockout_after_3_attempts_returns_423(async_client: AsyncClient):
    """Valida bloqueo temporal tras acumular 3 intentos fallidos consecutivos (Criterio 2)."""
    valid_totp = generate_totp(DEFAULT_SEED_TOTP_SECRET)

    # Intento 1
    r1 = await async_client.post(
        "/api/v1/experience/auth/login",
        json={"username": DEFAULT_SEED_USERNAME, "password": "Wrong1*", "totp_code": valid_totp},
    )
    assert r1.status_code == 401

    # Intento 2
    r2 = await async_client.post(
        "/api/v1/experience/auth/login",
        json={"username": DEFAULT_SEED_USERNAME, "password": "Wrong2*", "totp_code": valid_totp},
    )
    assert r2.status_code == 401

    # Intento 3 -> HTTP 423 Locked
    r3 = await async_client.post(
        "/api/v1/experience/auth/login",
        json={"username": DEFAULT_SEED_USERNAME, "password": "Wrong3*", "totp_code": valid_totp},
    )
    assert r3.status_code == 423
    assert "Cuenta bloqueada por seguridad" in r3.json()["detail"]
    assert "15 minutos" in r3.json()["detail"]

    # Intento adicional con credenciales válidas sigue bloqueado
    r4 = await async_client.post(
        "/api/v1/experience/auth/login",
        json={
            "username": DEFAULT_SEED_USERNAME,
            "password": DEFAULT_SEED_PASSWORD,
            "totp_code": valid_totp,
        },
    )
    assert r4.status_code == 423


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_token_flow(async_client: AsyncClient):
    """Valida renovación silenciosa con refresh token (Criterio 3)."""
    # 1. Login exitoso
    valid_totp = generate_totp(DEFAULT_SEED_TOTP_SECRET)
    login_resp = await async_client.post(
        "/api/v1/experience/auth/login",
        json={
            "username": DEFAULT_SEED_USERNAME,
            "password": DEFAULT_SEED_PASSWORD,
            "totp_code": valid_totp,
        },
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    # 2. Renovar sesión
    refresh_resp = await async_client.post(
        "/api/v1/experience/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert data["role"] == "advisor"
    assert data["advisor_name"] == DEFAULT_SEED_NAME

    # 3. Refresh token inválido retorna 401
    bad_refresh = await async_client.post(
        "/api/v1/experience/auth/refresh",
        json={"refresh_token": "token_invalido"},
    )
    assert bad_refresh.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_role_authorization_on_commercial_endpoints(async_client: AsyncClient):
    """Valida control de roles RBAC sobre endpoints comerciales (HA-13)."""
    client_payload = {
        "document_type": "CC",
        "document_number": "1020304050",
        "first_name": "Carlos",
        "last_name": "Perez",
        "birth_date": "1990-05-15",
        "email": "carlos@test.com",
        "phone": "3001234567",
    }

    # 1. Sin token -> 401 Unauthorized
    resp_no_token = await async_client.post(
        "/api/v1/experience/clients/validate",
        json=client_payload,
    )
    assert resp_no_token.status_code == 401

    # 2. Con rol no autorizado (ej. 'guest' o 'auditor') -> 403 Forbidden (HA-13)
    unauthorized_token = create_access_token(
        subject="invitado@solventa.com",
        role="guest",
    )
    resp_forbidden = await async_client.post(
        "/api/v1/experience/clients/validate",
        headers={"Authorization": f"Bearer {unauthorized_token}"},
        json=client_payload,
    )
    assert resp_forbidden.status_code == 403
    assert "Permisos insuficientes" in resp_forbidden.json()["detail"]

    # 3. Con rol 'advisor' -> Autorizado (pasa el middleware RBAC y llega al placeholder del servicio 501)
    advisor_token = create_access_token(
        subject=DEFAULT_SEED_USERNAME,
        role="advisor",
    )
    resp_authorized = await async_client.post(
        "/api/v1/experience/clients/validate",
        headers={"Authorization": f"Bearer {advisor_token}"},
        json=client_payload,
    )
    # Pasa la barrera de seguridad de roles y llega al endpoint (501 placeholder de HU-WEB-02)
    assert resp_authorized.status_code == 501

