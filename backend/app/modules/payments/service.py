"""Cobro de la prima: un solo cargo por clave y por póliza aunque se reintente (HU-WEB-06, HA-11)."""
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.idempotency import IdempotencyRecordDB, find_response, save_response
from app.core.outbox import OutboxMessageDB
from app.modules.payments.gateway import SimulatedGateway
from app.modules.payments.models import RECEIPT_NUMBER_SEQ, PaymentChargeRequest, PaymentReceipt, PaymentTransactionDB
from app.modules.policy.models import PolicyDB
from app.modules.policy.service import policy_service


class PaymentDeclinedError(Exception):
    pass


class PolicyAlreadyPaidError(Exception):
    pass


class AmountMismatchError(Exception):
    pass


def ensure_chargeable(policy: PolicyDB, request: PaymentChargeRequest) -> None:
    """Solo se cobra una póliza pendiente de pago, por su prima mensual exacta."""
    if policy.status == "ACTIVE":
        raise PolicyAlreadyPaidError()
    if request.amount != policy.conditions["monthly_premium"]:
        raise AmountMismatchError()


def new_transaction(request: PaymentChargeRequest, idempotency_key: str, partner_id: str) -> PaymentTransactionDB:
    """Cobro con los datos de la petición salvo el token, que nunca se guarda (HA-15)."""
    return PaymentTransactionDB(
        transaction_id=str(uuid.uuid4()),
        partner_id=partner_id,
        idempotency_key=idempotency_key,
        created_at=datetime.now(timezone.utc),
        **request.model_dump(exclude={"token_or_account"}),
    )


def decline(transaction: PaymentTransactionDB, reason: str) -> Tuple[HTTPStatus, dict]:
    """La póliza sigue pendiente de pago y el motivo vuelve al asesor para que ofrezca otro medio."""
    transaction.status, transaction.decline_reason = "DECLINED", reason
    return HTTPStatus.PAYMENT_REQUIRED, {"detail": f"Pago rechazado: {reason}. Intente con otro medio de pago."}


async def approve(session: AsyncSession, transaction: PaymentTransactionDB, policy: PolicyDB) -> Tuple[HTTPStatus, dict]:
    """Numera el recibo, activa la póliza y deja el evento PaymentApproved para el correo de confirmación."""
    sequence = await session.scalar(select(RECEIPT_NUMBER_SEQ.next_value()))
    transaction.status = "APPROVED"
    transaction.receipt_number = f"REC-{transaction.created_at.year}-{sequence:05d}"
    receipt = PaymentReceipt.model_validate(transaction).model_dump(mode="json")
    policy_service.activate(policy)
    session.add(OutboxMessageDB(aggregate_id=transaction.transaction_id, event_type="PaymentApproved", payload=receipt))
    return HTTPStatus.OK, receipt


def replay(record: IdempotencyRecordDB) -> PaymentReceipt:
    """Respuesta guardada del cobro: el recibo si se aprobó, el mismo rechazo si no."""
    if record.response_status == HTTPStatus.PAYMENT_REQUIRED:
        raise PaymentDeclinedError(record.response_body["detail"])
    return PaymentReceipt.model_validate(record.response_body)


class PaymentService:
    """Cobra con la póliza bloqueada, para que sus cobros se atiendan de uno en uno."""

    def __init__(self, gateway):
        self.gateway = gateway

    async def process_charge(
        self, session: AsyncSession, request: PaymentChargeRequest, idempotency_key: str, partner_id: str = "default"
    ) -> PaymentReceipt:
        """Cobra la prima una sola vez; con una clave ya usada repite su respuesta sin volver a la pasarela."""
        policy = await policy_service.lock(session, request.policy_number)
        saved = await find_response(session, partner_id, idempotency_key, request)
        return replay(saved or await self.charge(session, policy, request, idempotency_key, partner_id))

    async def charge(
        self, session: AsyncSession, policy: PolicyDB, request: PaymentChargeRequest, idempotency_key: str,
        partner_id: str,
    ) -> IdempotencyRecordDB:
        """Cobra en la pasarela y confirma en una transacción el cobro, la póliza, la respuesta y el evento."""
        ensure_chargeable(policy, request)
        transaction = new_transaction(request, idempotency_key, partner_id)
        reason = await self.gateway.charge(idempotency_key, request.amount, request.token_or_account)
        status, body = decline(transaction, reason) if reason else await approve(session, transaction, policy)
        session.add(transaction)
        record = save_response(session, partner_id, idempotency_key, request, status, body)
        await session.commit()
        return record


payment_service = PaymentService(SimulatedGateway())
