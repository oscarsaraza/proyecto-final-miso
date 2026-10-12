"""Modelos de datos para el motor de cotización y tarificación."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, Float, String
from app.core.database import Base


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


class PremiumFactor(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "age"})
    label: str = Field(..., json_schema_extra={"example": "Ajuste por edad"})
    multiplier: float = Field(..., description="Multiplicador aplicado; 1.0 en la tarifa base")
    amount: float = Field(..., description="Aporte en pesos a la prima mensual; negativo si la reduce")


class QuoteTierDetail(BaseModel):
    tier: PlanTier
    monthly_premium: float
    annual_premium: float
    coverages: List[Coverage]
    breakdown: List[PremiumFactor] = Field(default_factory=list)


class QuoteResponse(BaseModel):
    quote_id: str
    document_number: str
    status: str = Field(..., description="'active' o 'degraded' si el buró no respondió a tiempo")
    degradation_reason: Optional[str] = Field(None, description="'TIMEOUT_EXCEEDED' cuando status es 'degraded'")
    score_applied: float
    tiers: List[QuoteTierDetail]
    created_at: str
    expires_at: str


class QuoteDB(Base):
    """Cotización calculada, con su traza de degradación; la emisión comprueba aquí su vigencia (HU-WEB-05)."""
    __tablename__ = "quotes"

    quote_id = Column(String(16), primary_key=True)
    document_number = Column(String, nullable=False)
    status = Column(String(16), nullable=False)
    degradation_reason = Column(String(32), nullable=True)
    score_applied = Column(Float, nullable=False)
    tiers = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
