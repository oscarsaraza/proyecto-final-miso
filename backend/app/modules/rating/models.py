"""Modelos de datos para el motor de cotización y canal de socios B2B (HU-WEB-10)."""
from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, func
from app.core.database import Base


class PlanTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class PartnerStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


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


class PartnerTokenRequest(BaseModel):
    client_id: str = Field(
        ...,
        min_length=1,
        description="Identificador de cliente OAuth2 del socio de distribución",
        json_schema_extra={"example": "banco_aliado"},
    )
    client_secret: str = Field(
        ...,
        min_length=1,
        description="Secreto del cliente OAuth2 asignado al socio",
        json_schema_extra={"example": "AliadoSecret2026*"},
    )
    grant_type: Literal["client_credentials"] = Field(
        default="client_credentials",
        description="Flujo OAuth2 machine-to-machine para socios B2B",
        json_schema_extra={"example": "client_credentials"},
    )


class PartnerTokenResponse(BaseModel):
    access_token: str = Field(..., description="Token JWT firmado para consumir la API de Quote Edge")
    token_type: str = Field(default="bearer", json_schema_extra={"example": "bearer"})
    expires_in: int = Field(
        ...,
        description="Tiempo de vigencia del token en segundos",
        json_schema_extra={"example": 3600},
    )
    partner_id: str = Field(
        ...,
        description="Identificador único del socio autenticado",
        json_schema_extra={"example": "banco-aliado-1"},
    )


class PartnerQuoteResponse(QuoteResponse):
    partner_id: str = Field(
        ...,
        description="Identificador del socio propietario de la cotización",
        json_schema_extra={"example": "banco-aliado-1"},
    )

    @classmethod
    def from_db(cls, quote: "QuoteDB") -> "PartnerQuoteResponse":
        """Construye la respuesta pública a partir del registro relacional QuoteDB."""
        created_iso = (
            quote.created_at.isoformat()
            if isinstance(quote.created_at, datetime)
            else str(quote.created_at)
        )
        expires_iso = (
            quote.expires_at.isoformat()
            if isinstance(quote.expires_at, datetime)
            else str(quote.expires_at)
        )
        return cls(
            quote_id=quote.quote_id,
            partner_id=quote.partner_id or "",
            document_number=quote.document_number,
            status=quote.status,
            degradation_reason=quote.degradation_reason,
            score_applied=quote.score_applied,
            tiers=[QuoteTierDetail.model_validate(tier) for tier in quote.tiers],
            created_at=created_iso,
            expires_at=expires_iso,
        )


class PartnerDB(Base):
    """Socio de distribución B2B habilitado para cotizar con credenciales propias (HU-WEB-10)."""
    __tablename__ = "partners"

    partner_id = Column(String(64), primary_key=True, index=True)
    client_id = Column(String(64), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=False)
    name = Column(String(120), nullable=False)
    status = Column(String(32), nullable=False, default=PartnerStatus.ACTIVE.value)
    quota_limit = Column(Integer, nullable=False, default=50000)
    quota_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class QuoteDB(Base):
    """Cotización calculada, con su traza de degradación y confinamiento opcional por socio (HU-WEB-05, HU-WEB-10)."""
    __tablename__ = "quotes"

    quote_id = Column(String(16), primary_key=True)
    partner_id = Column(String(64), nullable=True, index=True)
    document_number = Column(String, nullable=False)
    status = Column(String(16), nullable=False)
    degradation_reason = Column(String(32), nullable=True)
    score_applied = Column(Float, nullable=False)
    tiers = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
