"""Modelos de datos para identificación de cliente y consentimiento Open Finance."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


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
    document_number: str
    channel: str = Field(default="web", json_schema_extra={"example": "web"})
    otp_code: str = Field(..., min_length=6, max_length=6, json_schema_extra={"example": "839201"})
    terms_accepted: bool = Field(..., json_schema_extra={"example": True})


class ConsentRecord(BaseModel):
    consent_id: str
    document_number: str
    status: str = Field(default="GRANTED")
    consent_hash: str
    granted_at: str
