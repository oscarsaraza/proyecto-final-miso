"""Modelos de datos para cobro y transacciones financieras."""
import uuid
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, UniqueConstraint
from app.core.database import Base


class PaymentTransactionDB(Base):
    """Intento de cobro de una póliza, aprobado o rechazado; no guarda el token del medio de pago (HA-15)."""
    __tablename__ = "payment_transactions"
    __table_args__ = (UniqueConstraint("partner_id", "idempotency_key"),)

    transaction_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String(64), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    policy_number = Column(String(16), ForeignKey("policies.policy_number"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    payment_method = Column(String(16), nullable=False)
    status = Column(String(16), nullable=False)
    decline_reason = Column(String, nullable=True)
    receipt_number = Column(String(16), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class PaymentChargeRequest(BaseModel):
    quote_id: str
    policy_number: str
    amount: float = Field(..., gt=0)
    currency: str = Field(default="COP")
    payment_method: str = Field(..., json_schema_extra={"example": "PSE"})
    token_or_account: str = Field(..., json_schema_extra={"example": "bank_code_1022"})


class PaymentReceipt(BaseModel):
    transaction_id: str
    idempotency_key: str
    policy_number: str
    amount: float
    status: str = Field(default="APPROVED")
    receipt_number: str
    created_at: str
