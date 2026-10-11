"""Modelos de identidad del asegurado para el canal móvil."""
from pydantic import BaseModel, Field


class OtpRequest(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "maria.ruiz@correo.co"})


class OtpResponse(BaseModel):
    message: str
    expires_in: int
    debug_code: str | None = Field(default=None, description="Solo en desarrollo: simula el SMS")


class InsuredLoginRequest(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "maria.ruiz@correo.co"})
    password: str = Field(..., json_schema_extra={"example": "Solventa2026!"})
    otp_code: str = Field(..., min_length=6, max_length=6, json_schema_extra={"example": "417902"})


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    full_name: str
