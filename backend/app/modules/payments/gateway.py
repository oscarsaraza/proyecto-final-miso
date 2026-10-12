"""Pasarela de pagos simulada: no hay integración real ni datos de tarjeta, solo tokens (HA-15)."""
from typing import Dict, Optional

# Tokens de prueba que el banco rechaza, con su motivo.
DECLINED_TOKENS = {"tok_insufficient_funds": "fondos insuficientes"}


class GatewayUnavailableError(Exception):
    pass


class SimulatedGateway:
    """Aprueba todo token salvo los rechazados de prueba; la misma clave devuelve su resultado sin cobrar otra vez."""

    def __init__(self):
        self.charges: Dict[str, Optional[str]] = {}

    async def charge(self, idempotency_key: str, amount: float, token: str) -> Optional[str]:
        """Motivo del rechazo, o None si el cargo se aprobó."""
        return self.charges.setdefault(idempotency_key, DECLINED_TOKENS.get(token))
