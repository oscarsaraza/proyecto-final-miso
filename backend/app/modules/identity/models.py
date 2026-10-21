"""Modelos de identidad del asegurado para el canal móvil."""
from datetime import datetime

from pydantic import BaseModel, Field


class OtpRequest(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "maria.ruiz@correo.co"})


class OtpResponse(BaseModel):
    message: str
    expires_in: int
    debug_code: str | None = Field(default=None, description="Solo con SMS_PROVIDER=console: simula el SMS")


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


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class DeviceRegistrationResponse(BaseModel):
    device_id: str
    device_secret: str


class BiometricLoginRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=36)
    device_secret: str = Field(..., min_length=1, max_length=128)


class PasswordForgotRequest(BaseModel):
    email: str


class PasswordResetRequest(BaseModel):
    email: str
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=1, max_length=128)


class MessageResponse(BaseModel):
    message: str


class LockedResponse(BaseModel):
    detail: str
    locked_until: datetime
    retry_after: int
