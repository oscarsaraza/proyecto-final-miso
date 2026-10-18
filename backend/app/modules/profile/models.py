"""Modelos de datos para identificación de cliente y consentimiento Open Finance."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, Integer, String
from app.core.database import Base


class ClientIdentification(BaseModel):
    document_type: str = Field(..., json_schema_extra={"example": "CC"})
    document_number: str = Field(..., min_length=5, max_length=20, json_schema_extra={"example": "1020304050"})
    first_name: str = Field(..., min_length=2, json_schema_extra={"example": "Carlos"})
    last_name: str = Field(..., min_length=2, json_schema_extra={"example": "Rodriguez"})
    birth_date: date = Field(..., json_schema_extra={"example": "1988-04-12"})
    email: str = Field(..., json_schema_extra={"example": "carlos.rodriguez@email.com"})
    phone: str = Field(..., json_schema_extra={"example": "3001234567"})

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))


class ConsentRequest(BaseModel):
    document_number: str = Field(..., min_length=5, max_length=20, json_schema_extra={"example": "1020304050"})
    channel: str = Field(default="web", min_length=2, json_schema_extra={"example": "web"})
    otp_code: str = Field(..., pattern=r"^\d{6}$", json_schema_extra={"example": "839201"})
    terms_accepted: bool = Field(..., json_schema_extra={"example": True})
    purpose: str = Field(
        default="Perfilamiento y cotización de seguro de vida hipotecario con Open Finance",
        min_length=3,
        json_schema_extra={"example": "Perfilamiento y cotización de seguro de vida hipotecario con Open Finance"},
    )
    scope: str = Field(
        default="Historial crediticio, capacidad de endeudamiento y scoring financiero",
        min_length=3,
        json_schema_extra={"example": "Historial crediticio, capacidad de endeudamiento y scoring financiero"},
    )
    validity_days: int = Field(default=30, ge=1, le=365, json_schema_extra={"example": 30})


class ConsentRecord(BaseModel):
    consent_id: str
    document_number: str
    channel: str = "web"
    purpose: str
    scope: str
    validity_days: int
    status: str = Field(default="GRANTED")
    consent_hash: str
    granted_at: str
    expires_at: str


# --- Modelos SQLAlchemy de Catálogos (PostgreSQL) ---

class FinancialEntityDB(Base):
    """Entidad financiera / establecimiento bancario vigilado en Colombia."""
    __tablename__ = "financial_entities"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class CityDB(Base):
    """Ciudad o municipio de residencia en Colombia."""
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


# --- DTOs Pydantic para Catálogos ---

class FinancialEntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    is_active: bool


class CityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    is_active: bool
