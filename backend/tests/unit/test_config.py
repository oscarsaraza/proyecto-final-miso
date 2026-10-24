"""Configuración de producción: llaves obligatorias y distintas, errores sin valores (HOTFIX-configuracion-de-produccion)."""
import hashlib
import hmac
import secrets

import pytest

from app.core.config import MIN_KEY_LENGTH, load_settings, settings
from app.main import docs_urls
from app.modules.identity.service import InsuredAuthService

pytestmark = pytest.mark.unit


def llaves(**extra) -> dict:
    return {"JWT_SECRET_KEY": secrets.token_urlsafe(48), "OTP_SECRET_KEY": secrets.token_urlsafe(48), **extra}


def test_tc_01_sin_llaves_no_arranca_y_no_muestra_valores(monkeypatch):
    canario = "canario-" + secrets.token_hex(16)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("OTP_SECRET_KEY", raising=False)
    monkeypatch.setenv("DB_PASSWORD", canario)

    with pytest.raises(RuntimeError) as error:
        load_settings(_env_file=None)

    mensaje = str(error.value)
    assert "JWT_SECRET_KEY" in mensaje and "OTP_SECRET_KEY" in mensaje
    assert canario not in mensaje
    assert error.value.__cause__ is None and error.value.__suppress_context__


def test_tc_02_llave_corta_se_rechaza_y_la_minima_se_acepta():
    corta = "x" * (MIN_KEY_LENGTH - 1)
    with pytest.raises(RuntimeError) as error:
        load_settings(_env_file=None, **llaves(JWT_SECRET_KEY=corta))
    assert "JWT_SECRET_KEY" in str(error.value)
    assert corta not in str(error.value)

    minima = secrets.token_hex(MIN_KEY_LENGTH // 2)
    assert load_settings(_env_file=None, **llaves(JWT_SECRET_KEY=minima)).JWT_SECRET_KEY.get_secret_value() == minima


def test_tc_03_llaves_iguales_se_rechazan():
    misma = secrets.token_urlsafe(48)
    with pytest.raises(RuntimeError) as error:
        load_settings(_env_file=None, JWT_SECRET_KEY=misma, OTP_SECRET_KEY=misma)
    assert "distintas" in str(error.value)
    assert misma not in str(error.value)


def test_tc_04_el_codigo_se_firma_con_la_llave_otp():
    mensaje = b"usuario-1:login:123456"
    con_otp = hmac.new(settings.OTP_SECRET_KEY.get_secret_value().encode(), mensaje, hashlib.sha256).hexdigest()
    con_jwt = hmac.new(settings.JWT_SECRET_KEY.get_secret_value().encode(), mensaje, hashlib.sha256).hexdigest()

    assert InsuredAuthService._code_hash("usuario-1", "login", "123456") == con_otp
    assert con_otp != con_jwt


def test_tc_05_cors_y_documentacion_segun_configuracion(monkeypatch):
    assert load_settings(_env_file=None, **llaves()).CORS_ORIGINS == []
    monkeypatch.setenv("CORS_ORIGINS", '["https://portal.example.com"]')
    assert load_settings(_env_file=None, **llaves()).CORS_ORIGINS == ["https://portal.example.com"]

    assert load_settings(_env_file=None, **llaves(ENVIRONMENT="production")).debug_enabled is False
    assert load_settings(_env_file=None, **llaves()).debug_enabled is True
    assert docs_urls(False) == {"docs_url": None, "redoc_url": None, "openapi_url": None}
    assert docs_urls(True)["openapi_url"] == "/openapi.json"
