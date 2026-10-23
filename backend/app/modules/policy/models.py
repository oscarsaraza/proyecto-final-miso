"""Modelos de datos para la emisión de pólizas."""
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Sequence, String
from app.core.database import Base
from app.modules.rating.models import PlanTier, QuoteTierDetail

# Consecutivo global del número POL-YYYY-XXXXX; los saltos por emisiones repetidas no importan.
POLICY_NUMBER_SEQ = Sequence("policy_number_seq", metadata=Base.metadata)


class PolicyDB(Base):
    """Póliza emitida; copia el plan cotizado para que sus condiciones no cambien después (HA-16)."""
    __tablename__ = "policies"

    policy_number = Column(String(16), primary_key=True)
    quote_id = Column(String(16), ForeignKey("quotes.quote_id"), unique=True, nullable=False)
    insured_document = Column(String, nullable=False)
    beneficiaries = Column(JSON, nullable=False)
    conditions = Column(JSON, nullable=False)
    status = Column(String(16), nullable=False, default="ISSUED")
    issued_at = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)


class PolicyIssueRequest(BaseModel):
    quote_id: str
    tier: PlanTier
    beneficiaries: List[dict] = Field(default_factory=list)


class PolicyRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    policy_number: str
    quote_id: str
    insured_document: str
    conditions: QuoteTierDetail
    status: str = Field(default="ISSUED")
    issued_at: datetime
    valid_until: datetime
    pdf_s3_key: Optional[str] = Field(None, description="Carátula en S3; llega con HU-WEB-16")


class CardCoverage(BaseModel):
    name: str
    limit: float


class InsuredPolicyCard(BaseModel):
    """Tarjeta de la billetera: sin documento, beneficiarios ni prima (HU-MOV-04)."""
    policy_number: str
    plan: PlanTier
    holder_name: str
    coverages: List[CardCoverage]
    valid_from: datetime
    valid_until: datetime


class InsuredPolicies(BaseModel):
    policies: List[InsuredPolicyCard]
