"""Servicio del motor actuarial de cotización (Placeholder para HU-WEB-03 y HU-WEB-04)."""
from typing import Optional
from app.core.config import settings
from app.modules.rating.models import QuoteRequest, QuoteResponse


class RatingService:
    """Motor actuarial en memoria con protección de latencia (ASR-01, ASR-02, HA-01, HA-05)."""

    def __init__(self, bureau_timeout: float = settings.BUREAU_TIMEOUT_SECONDS):
        self.bureau_timeout = bureau_timeout

    async def calculate_quote(
        self,
        request: QuoteRequest,
        simulated_bureau_delay: float = 0.0,
    ) -> QuoteResponse:
        """Calcula cotización en memoria. Ante timeout (> 400ms) activa fallback conservador.

        A ser implementado durante HU-WEB-03 (Tarificación) y HU-WEB-04 (Degradación).
        """
        raise NotImplementedError("calculate_quote pendiente de implementación en HU-WEB-03 y HU-WEB-04")


rating_service = RatingService()
