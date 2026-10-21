"""Envío de SMS: consola en desarrollo y Twilio cuando hay credenciales (HU-MOV-02)."""
from typing import Optional, Protocol

import httpx

from app.core.config import settings

TWILIO_API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


class SmsDeliveryError(Exception):
    pass


class SmsSender(Protocol):
    exposes_code: bool

    async def send(self, to: str, body: str) -> None: ...


class ConsoleSmsSender:
    """No envía nada: el código se devuelve en la respuesta como código de prueba."""

    exposes_code = True

    async def send(self, to: str, body: str) -> None:
        return None


class TwilioSmsSender:
    exposes_code = False

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        transport: Optional[httpx.AsyncBaseTransport] = None,
        timeout: float = 5.0,
    ):
        self._url = TWILIO_API.format(sid=account_sid)
        self._auth = (account_sid, auth_token)
        self._from = from_number
        self._transport = transport
        self._timeout = timeout

    async def send(self, to: str, body: str) -> None:
        try:
            async with httpx.AsyncClient(transport=self._transport, timeout=self._timeout) as client:
                response = await client.post(
                    self._url, data={"To": to, "From": self._from, "Body": body}, auth=self._auth
                )
        except httpx.HTTPError as exc:
            raise SmsDeliveryError("Twilio no respondió") from exc
        if response.status_code >= 400:
            raise SmsDeliveryError(f"Twilio rechazó el envío ({response.status_code})")


def get_sms_sender() -> SmsSender:
    if settings.SMS_PROVIDER == "twilio":
        if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
            raise RuntimeError("SMS_PROVIDER=twilio requiere TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_FROM_NUMBER")
        return TwilioSmsSender(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_FROM_NUMBER)
    return ConsoleSmsSender()
