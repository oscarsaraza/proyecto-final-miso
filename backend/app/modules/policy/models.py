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
    partner_id = Column(String, ForeignKey("partners.partner_id"), nullable=True, index=True)
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
    partner_id: Optional[str] = None
    insured_document: str
    conditions: QuoteTierDetail
    status: str = Field(default="ISSUED")
    issued_at: datetime
    valid_until: datetime
    pdf_s3_key: Optional[str] = Field(None, description="Carátula en S3; llega con HU-WEB-16")


class PartnerPolicyIssueRequest(BaseModel):
    """Solicitud de emisión B2B desde el canal del socio (HU-WEB-14)."""
    quote_id: str = Field(..., description="Identificador de la cotización calculada por el socio")
    tier: PlanTier = Field(..., description="Nivel de plan seleccionado para la emisión")
    beneficiaries: List[dict] = Field(default_factory=list, description="Beneficiarios designados por el asegurado")


class PartnerPolicyResponse(BaseModel):
    """Proyección de lectura CQRS de la póliza emitida confinada al socio B2B (HU-WEB-14, HA-04, HA-14)."""
    model_config = ConfigDict(from_attributes=True)

    policy_number: str = Field(..., description="Número oficial de póliza POL-YYYY-XXXXX")
    quote_id: str = Field(..., description="ID de la cotización origen")
    partner_id: str = Field(..., description="ID del socio B2B propietario de la emisión")
    insured_document: str = Field(..., description="Número de documento del asegurado")
    conditions: QuoteTierDetail = Field(..., description="Condiciones del plan contratado")
    status: str = Field(default="ISSUED", description="Estado de la póliza (ISSUED, ACTIVE, CANCELLED)")
    issued_at: datetime = Field(..., description="Fecha y hora de emisión")
    valid_until: datetime = Field(..., description="Fecha y hora de fin de vigencia (1 año)")
    pdf_s3_key: Optional[str] = Field(None, description="Clave S3 del certificado PDF (HU-WEB-16)")
