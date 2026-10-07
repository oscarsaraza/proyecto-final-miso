"""Servicio de pagos con garantía de idempotencia estricta (Placeholder para HU-WEB-06)."""
from typing import Optional
from app.modules.payments.models import PaymentChargeRequest, PaymentReceipt


class PaymentService:
    def process_charge(
        self,
        request: PaymentChargeRequest,
        idempotency_key: str,
        partner_id: Optional[str] = None,
    ) -> PaymentReceipt:
        """Procesa el cobro de la prima garantizando cero duplicación mediante Idempotency-Key.

        A ser implementado durante HU-WEB-06 (Recaudo con idempotencia).
        """
        raise NotImplementedError("process_charge pendiente de implementación en HU-WEB-06")


payment_service = PaymentService()
