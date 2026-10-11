"""Modelos de datos y entidades SQLAlchemy para autenticación y usuarios (HU-WEB-13)."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from app.core.database import Base


class UserDB(Base):
    """Modelo de base de datos relacional para usuarios corporativos (PostgreSQL)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    totp_secret = Column(String(64), nullable=False)
    role = Column(String(50), nullable=False, default="advisor")
    full_name = Column(String(150), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# --- DTOs Pydantic para APIs ---

class LoginRequest(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "asesor@solventa.com"})
    password: str = Field(..., json_schema_extra={"example": "SuperSecreta2026*"})
    totp_code: str = Field(..., min_length=6, max_length=6, json_schema_extra={"example": "123456"})


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    advisor_name: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: str
    is_active: bool

