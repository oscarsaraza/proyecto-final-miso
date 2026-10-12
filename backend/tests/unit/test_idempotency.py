"""Pruebas unitarias de integridad transaccional e idempotencia en cobros (TC-S1-08)."""
import pytest


@pytest.mark.unit
@pytest.mark.skip(reason="TDD: Se habilitará al implementar HU-WEB-06 (Pago con idempotencia)")
def test_payment_charge_idempotency():
    """TC-S1-08: Valida que reintentos de pago con la misma Idempotency-Key retornen el mismo recibo."""
    pass
