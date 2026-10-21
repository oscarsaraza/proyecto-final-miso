"""Envío del código del asegurado por SMS (HU-MOV-02).

Por ahora solo existe el modo "console": no se envía nada y la app muestra el código de prueba.
Un proveedor real (por ejemplo AWS SNS) se agrega implementando SmsSender y eligiéndolo con SMS_PROVIDER.
"""
from typing import Protocol

from app.core.config import settings


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


def get_sms_sender() -> SmsSender:
    if settings.SMS_PROVIDER == "console":
        return ConsoleSmsSender()
    raise RuntimeError(f"SMS_PROVIDER={settings.SMS_PROVIDER} no está soportado; use SMS_PROVIDER=console")
