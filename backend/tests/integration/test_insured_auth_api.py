"""Pruebas de integración del login del asegurado en el BFF (TC-S1-10)."""
import pytest
from httpx import AsyncClient

EMAIL = "maria.ruiz@correo.co"
PASSWORD = "Solventa2026!"


async def request_code(client: AsyncClient) -> str:
    response = await client.post("/api/v1/auth/otp", json={"email": EMAIL})
    assert response.status_code == 200
    return response.json()["debug_code"]


@pytest.mark.integration
async def test_tc_s1_10_login_con_contrasena_y_codigo(async_client: AsyncClient):
    code = await request_code(async_client)

    response = await async_client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD, "otp_code": code}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["full_name"] == "María Ruiz"


@pytest.mark.integration
async def test_tc_s1_10_otp_no_revela_si_el_correo_existe(async_client: AsyncClient):
    response = await async_client.post("/api/v1/auth/otp", json={"email": "nadie@correo.co"})

    assert response.status_code == 200
    assert response.json()["debug_code"] is None


@pytest.mark.integration
async def test_tc_s1_10_credenciales_invalidas_responden_401_y_bloqueo_423(async_client: AsyncClient):
    code = await request_code(async_client)
    payload = {"email": EMAIL, "password": "otra-clave", "otp_code": code}

    first = await async_client.post("/api/v1/auth/login", json=payload)
    second = await async_client.post("/api/v1/auth/login", json=payload)
    third = await async_client.post("/api/v1/auth/login", json=payload)

    assert first.status_code == 401
    assert second.status_code == 401
    assert third.status_code == 423


@pytest.mark.integration
async def test_tc_s1_10_codigo_con_formato_invalido_responde_422(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD, "otp_code": "12"}
    )

    assert response.status_code == 422
