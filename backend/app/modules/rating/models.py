"""Modelos de datos para el motor de cotización y tarificación."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PlanTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class Coverage(BaseModel):
    id: str
    name: str
    limit: float
    deductible: float
    optional: bool = False
    included: bool = True


class QuoteRequest(BaseModel):
    document_type: str = Field(..., json_schema_extra={"example": "CC"})
    document_number: str = Field(..., json_schema_extra={"example": "123456789"})
    birth_date: str = Field(..., json_schema_extra={"example": "1990-05-15"})
    insured_amount: float = Field(..., gt=0, json_schema_extra={"example": 150000000.0})
    city: str = Field(default="Bogota")
    occupation_risk: int = Field(default=1, ge=1, le=5)


class QuoteTierDetail(BaseModel):
    tier: PlanTier
    monthly_premium: float
    annual_premium: float
    coverages: List[Coverage]


class QuoteResponse(BaseModel):
    quote_id: str
    document_number: str
    status: str = Field(..., description="'active' o 'degraded' (cuando se activa fallback)")
    score_applied: float
    tiers: List[QuoteTierDetail]
    created_at: str
    expires_at: str
