"""Envío del código del asegurado (HU-MOV-02)."""
import pytest

from app.core import sms
from app.core.sms import ConsoleSmsSender, get_sms_sender


@pytest.mark.unit
async def test_modo_consola_no_envia_y_expone_el_codigo_de_prueba():
    sender = ConsoleSmsSender()

    assert await sender.send("+573000000000", "Solventa: su código es 123456.") is None
    assert sender.exposes_code is True


@pytest.mark.unit
def test_proveedor_no_soportado_falla_con_mensaje_claro(monkeypatch):
    monkeypatch.setattr(sms.settings, "SMS_PROVIDER", "twilio")

    with pytest.raises(RuntimeError, match="SMS_PROVIDER=twilio no está soportado"):
        get_sms_sender()


@pytest.mark.unit
def test_por_defecto_usa_el_modo_consola(monkeypatch):
    monkeypatch.setattr(sms.settings, "SMS_PROVIDER", "console")

    assert isinstance(get_sms_sender(), ConsoleSmsSender)
