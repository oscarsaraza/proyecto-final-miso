"""Pruebas de integración del acceso del asegurado en el BFF (TC-S1-10, TC-S1-12)."""
import pytest
from httpx import AsyncClient

from tests.conftest import INSURED_EMAIL as EMAIL, INSURED_PASSWORD as PASSWORD

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("seeded_insured")]


async def request_code(client: AsyncClient, ip: str = "10.0.0.1") -> str:
    response = await client.post("/api/v1/auth/otp", json={"email": EMAIL}, headers={"X-Forwarded-For": ip})
    assert response.status_code == 200
    return response.json()["debug_code"]


async def login(client: AsyncClient) -> dict:
    code = await request_code(client)
    response = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD, "otp_code": code})
    assert response.status_code == 200
    return response.json()


def bearer(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_tc_s1_10_login_con_contrasena_y_codigo(async_client: AsyncClient):
    body = await login(async_client)

    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["full_name"] == "María Ruiz"


async def test_tc_s1_10_otp_no_revela_si_el_correo_existe(async_client: AsyncClient):
    response = await async_client.post("/api/v1/auth/otp", json={"email": "nadie@correo.co"})

    assert response.status_code == 200
    assert response.json()["debug_code"] is None


async def test_tc_s1_10_quinto_intento_fallido_responde_423_con_retry_after(async_client: AsyncClient):
    payload = {"email": EMAIL, "password": "otra-clave", "otp_code": "000000"}

    statuses = [(await async_client.post("/api/v1/auth/login", json=payload)).status_code for _ in range(4)]
    locked = await async_client.post("/api/v1/auth/login", json=payload)

    assert statuses == [401, 401, 401, 401]
    assert locked.status_code == 423
    assert locked.headers["Retry-After"] == "900"
    assert locked.json()["retry_after"] == 900 and locked.json()["locked_until"]


async def test_tc_s1_10_reenviar_codigo_antes_de_un_minuto_responde_429(async_client: AsyncClient):
    await request_code(async_client)

    response = await async_client.post("/api/v1/auth/otp", json={"email": EMAIL})

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0


async def test_tc_s1_10_codigo_con_formato_invalido_responde_422(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD, "otp_code": "12"}
    )

    assert response.status_code == 422


async def test_tc_s1_12_logout_revoca_la_sesion(async_client: AsyncClient):
    tokens = await login(async_client)

    logout = await async_client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    refresh = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert logout.status_code == 204
    assert refresh.status_code == 401


async def test_tc_s1_12_refresh_sin_logout_renueva_tokens(async_client: AsyncClient):
    tokens = await login(async_client)

    response = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_tc_s1_12_logout_con_token_invalido_responde_401(async_client: AsyncClient):
    response = await async_client.post("/api/v1/auth/logout", json={"refresh_token": "no-es-un-jwt"})

    assert response.status_code == 401


async def test_tc_s1_12_huella_entra_despues_de_cerrar_sesion_y_se_desactiva(async_client: AsyncClient):
    tokens = await login(async_client)
    device = (await async_client.post("/api/v1/auth/devices", headers=bearer(tokens))).json()
    await async_client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})

    again = await async_client.post("/api/v1/auth/biometric", json=device)
    assert again.status_code == 200

    revoked = await async_client.delete(f"/api/v1/auth/devices/{device['device_id']}", headers=bearer(again.json()))
    rejected = await async_client.post("/api/v1/auth/biometric", json=device)
    assert revoked.status_code == 204
    assert rejected.status_code == 401


async def test_tc_s1_12_registrar_dispositivo_exige_access_token(async_client: AsyncClient):
    tokens = await login(async_client)

    without = await async_client.post("/api/v1/auth/devices")
    with_refresh = await async_client.post(
        "/api/v1/auth/devices", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )

    assert without.status_code == 401
    assert with_refresh.status_code == 401


async def test_recuperar_contrasena_por_codigo(async_client: AsyncClient):
    code = (await async_client.post("/api/v1/auth/password/forgot", json={"email": EMAIL})).json()["debug_code"]

    weak = await async_client.post(
        "/api/v1/auth/password/reset", json={"email": EMAIL, "code": code, "new_password": "corta"}
    )
    ok = await async_client.post(
        "/api/v1/auth/password/reset", json={"email": EMAIL, "code": code, "new_password": "NuevaClave2026"}
    )

    assert weak.status_code == 422
    assert ok.status_code == 200


async def test_mensajes_no_revelan_si_el_correo_existe(async_client: AsyncClient):
    real = await async_client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": "otra-clave", "otp_code": "000000"}
    )
    fake = await async_client.post(
        "/api/v1/auth/login", json={"email": "nadie@correo.co", "password": "otra-clave", "otp_code": "000000"}
    )

    assert real.status_code == fake.status_code == 401
    assert real.json() == fake.json()


async def test_recuperar_con_la_misma_contrasena_responde_409(async_client: AsyncClient):
    code = (await async_client.post("/api/v1/auth/password/forgot", json={"email": EMAIL})).json()["debug_code"]

    response = await async_client.post(
        "/api/v1/auth/password/reset", json={"email": EMAIL, "code": code, "new_password": PASSWORD}
    )

    assert response.status_code == 409
