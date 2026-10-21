"""Envío del código por SMS con Twilio (HU-MOV-02)."""
import httpx
import pytest

from app.core import sms
from app.core.sms import ConsoleSmsSender, SmsDeliveryError, TwilioSmsSender, get_sms_sender
from app.modules.identity.service import InsuredAuthService


def twilio(handler) -> TwilioSmsSender:
    return TwilioSmsSender("AC123", "token", "+15005550006", transport=httpx.MockTransport(handler))


@pytest.mark.unit
async def test_twilio_envia_destino_remitente_y_texto_con_autenticacion_basica():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers["authorization"]
        captured["body"] = request.content.decode()
        return httpx.Response(201, json={"sid": "SM1"})

    await twilio(handler).send("+573001112233", "Solventa: su código es 123456.")

    assert captured["url"] == "https://api.twilio.com/2010-04-01/Accounts/AC123/Messages.json"
    assert captured["auth"].startswith("Basic ")
    assert "To=%2B573001112233" in captured["body"]
    assert "From=%2B15005550006" in captured["body"]


@pytest.mark.unit
async def test_twilio_rechazo_se_reporta_como_error_de_envio():
    with pytest.raises(SmsDeliveryError):
        await twilio(lambda request: httpx.Response(400, json={"code": 21608})).send("+57300", "x")


@pytest.mark.unit
async def test_twilio_sin_conexion_se_reporta_como_error_de_envio():
    def handler(request):
        raise httpx.ConnectError("sin red")

    with pytest.raises(SmsDeliveryError):
        await twilio(handler).send("+57300", "x")


@pytest.mark.unit
def test_solo_la_consola_expone_el_codigo_de_prueba():
    assert ConsoleSmsSender.exposes_code is True
    assert TwilioSmsSender.exposes_code is False


@pytest.mark.unit
async def test_twilio_rechazo_sin_json_tambien_se_reporta():
    with pytest.raises(SmsDeliveryError):
        await twilio(lambda request: httpx.Response(500, text="<html>error</html>")).send("+57300", "x")


@pytest.mark.unit
def test_twilio_sin_credenciales_completas_falla_al_arrancar(monkeypatch):
    monkeypatch.setattr(sms.settings, "SMS_PROVIDER", "twilio")
    monkeypatch.setattr(sms.settings, "TWILIO_ACCOUNT_SID", "AC123")
    monkeypatch.setattr(sms.settings, "TWILIO_AUTH_TOKEN", None)
    monkeypatch.setattr(sms.settings, "TWILIO_FROM_NUMBER", None)

    with pytest.raises(RuntimeError, match="TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER"):
        get_sms_sender()


@pytest.mark.unit
def test_twilio_con_credenciales_completas(monkeypatch):
    monkeypatch.setattr(sms.settings, "SMS_PROVIDER", "twilio")
    monkeypatch.setattr(sms.settings, "TWILIO_ACCOUNT_SID", "AC123")
    monkeypatch.setattr(sms.settings, "TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setattr(sms.settings, "TWILIO_FROM_NUMBER", "+15005550006")

    assert isinstance(get_sms_sender(), TwilioSmsSender)


@pytest.mark.unit
def test_por_defecto_el_servicio_usa_el_codigo_de_prueba(monkeypatch):
    monkeypatch.setattr(sms.settings, "SMS_PROVIDER", "console")

    assert isinstance(InsuredAuthService().sms, ConsoleSmsSender)
