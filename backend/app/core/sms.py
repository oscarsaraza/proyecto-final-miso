"""Envío de SMS: consola por defecto y Twilio cuando hay credenciales (HU-MOV-02)."""
import logging
from typing import Optional, Protocol

import httpx

from app.core.config import settings

TWILIO_API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"

logger = logging.getLogger("uvicorn.error")


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
            logger.error("Twilio no respondió: %s", exc)
            raise SmsDeliveryError("Twilio no respondió") from exc
        if response.status_code >= 400:
            try:
                error = response.json()
                detail = f"código {error.get('code')}: {error.get('message')}"
            except ValueError:
                detail = response.text[:300]
            logger.error("Twilio rechazó el envío (%s) %s", response.status_code, detail)
            raise SmsDeliveryError(f"Twilio rechazó el envío ({response.status_code})")


def get_sms_sender() -> SmsSender:
    if settings.SMS_PROVIDER == "twilio":
        missing = [
            name
            for name in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER")
            if not getattr(settings, name)
        ]
        if missing:
            raise RuntimeError(f"SMS_PROVIDER=twilio pero faltan en la configuración: {', '.join(missing)}")
        return TwilioSmsSender(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_FROM_NUMBER)
    return ConsoleSmsSender()
