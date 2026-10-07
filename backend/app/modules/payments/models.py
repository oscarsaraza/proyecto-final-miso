"""Modelos de datos para cobro y transacciones financieras."""
from pydantic import BaseModel, Field
from typing import Optional


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
