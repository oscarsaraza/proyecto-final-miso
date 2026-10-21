"""Política contra fuerza bruta del acceso del asegurado (TC-S1-10)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.identity import policy

NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


@pytest.mark.unit
def test_bloqueo_creciente_15_30_60_minutos():
    assert policy.lock_duration(1) == timedelta(minutes=15)
    assert policy.lock_duration(2) == timedelta(minutes=30)
    assert policy.lock_duration(3) == timedelta(minutes=60)
    assert policy.lock_duration(9) == timedelta(minutes=60)


@pytest.mark.unit
def test_bloqueo_creciente_se_olvida_despues_de_un_dia():
    assert policy.effective_lock_count(2, NOW - timedelta(hours=25), NOW) == 0
    assert policy.effective_lock_count(2, NOW - timedelta(hours=1), NOW) == 2
    assert policy.effective_lock_count(2, None, NOW) == 2


@pytest.mark.unit
def test_pedir_codigo_exige_un_minuto_entre_envios():
    assert policy.otp_request_retry_after([], NOW) is None
    assert policy.otp_request_retry_after([NOW - timedelta(seconds=20)], NOW) == 40
    assert policy.otp_request_retry_after([NOW - timedelta(seconds=61)], NOW) is None


@pytest.mark.unit
def test_pedir_codigo_maximo_cinco_por_hora():
    times = [NOW - timedelta(minutes=m) for m in (50, 40, 30, 20, 10)]

    assert policy.otp_request_retry_after(times, NOW) == 10 * 60
    assert policy.otp_request_retry_after(times[1:], NOW) is None


@pytest.mark.unit
def test_ventana_por_ip_solo_cuenta_los_ultimos_15_minutos():
    viejos = [NOW - timedelta(minutes=20)] * 50
    recientes = [NOW - timedelta(minutes=5)] * 19

    assert policy.window_retry_after(viejos + recientes, 20, NOW) is None
    assert policy.window_retry_after(recientes + [NOW], 20, NOW) == 10 * 60


@pytest.mark.unit
@pytest.mark.parametrize(
    "password, ok",
    [("Solventa2026", True), ("corta1", False), ("sinnumeros", False), ("12345678", False)],
)
def test_contrasena_nueva_minimo_ocho_con_letras_y_numeros(password, ok):
    assert policy.is_strong_password(password) is ok


@pytest.mark.unit
def test_ip_real_detras_de_cloudflare_y_del_balanceador():
    assert policy.client_ip({"cf-connecting-ip": "1.1.1.1", "x-forwarded-for": "2.2.2.2"}, "3.3.3.3") == "1.1.1.1"
    assert policy.client_ip({"x-forwarded-for": "2.2.2.2, 10.0.0.1"}, "3.3.3.3") == "2.2.2.2"
    assert policy.client_ip({}, "3.3.3.3") == "3.3.3.3"
