"""Pruebas unitarias de integridad transaccional e idempotencia en cobros (TC-S1-08)."""
import pytest
from app.modules.payments.models import PaymentChargeRequest
from app.modules.payments.service import payment_service
from app.core.middleware import idempotency_store


@pytest.mark.unit
def test_payment_service_raises_not_implemented():
    """Valida que payment_service lance NotImplementedError antes de implementar HU-WEB-06."""
    charge_request = PaymentChargeRequest(
        quote_id="QUO-123456",
        policy_number="POL-2026-ABC123",
        amount=145000.0,
        currency="COP",
        payment_method="PSE",
        token_or_account="PSE_BANCOLOMBIA_01",
    )
    with pytest.raises(NotImplementedError):
        payment_service.process_charge(charge_request, idempotency_key="key-001")


@pytest.mark.unit
def test_idempotency_store_infrastructure():
    """Valida que la infraestructura transversal del almacén de idempotencia funcione correctamente (HA-11)."""
    hash_val = idempotency_store.compute_hash(b"test_payload")
    assert len(hash_val) == 64

    idempotency_store.save(
        partner_id="p1",
        idempotency_key="k1",
        request_hash=hash_val,
        status_code=200,
        response_body={"status": "OK"},
    )
    saved = idempotency_store.get("p1", "k1")
    assert saved is not None
    assert saved["status_code"] == 200


@pytest.mark.unit
@pytest.mark.skip(reason="TDD: Se habilitará al implementar HU-WEB-06 (Pago con idempotencia)")
def test_payment_charge_idempotency():
    """TC-S1-08: Valida que reintentos de pago con la misma Idempotency-Key retornen el mismo recibo."""
    pass
