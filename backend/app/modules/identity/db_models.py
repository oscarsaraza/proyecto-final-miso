"""Tablas de identidad del asegurado: compartidas por todas las réplicas (HU-MOV-02, HU-MOV-12)."""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, func

from app.core.database import Base


class InsuredAccountDB(Base):
    __tablename__ = "insured_accounts"

    user_id = Column(String(36), primary_key=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    document_number = Column(String(20), nullable=False)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    token_version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InsuredOtpDB(Base):
    __tablename__ = "insured_otps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("insured_accounts.user_id", ondelete="CASCADE"), nullable=False)
    purpose = Column(String(20), nullable=False)
    code_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_insured_otps_user_purpose", "user_id", "purpose"),)


class InsuredDeviceDB(Base):
    __tablename__ = "insured_devices"

    device_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("insured_accounts.user_id", ondelete="CASCADE"), nullable=False, index=True)
    secret_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class LoginLockDB(Base):
    """Intentos fallidos y bloqueo por correo, exista o no la cuenta, para no revelar cuáles existen."""

    __tablename__ = "login_locks"

    email = Column(String(254), primary_key=True)
    failed_attempts = Column(Integer, default=0, nullable=False)
    lock_count = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)


class RevokedTokenDB(Base):
    __tablename__ = "revoked_tokens"

    jti = Column(String(64), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class LoginAttemptDB(Base):
    """Auditoría de cada intento: de aquí salen los límites por IP y por cuenta."""

    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(254), nullable=False)
    user_id = Column(String(36), nullable=True)
    ip = Column(String(64), nullable=True)
    channel = Column(String(20), nullable=False)
    result = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_login_attempts_email_created", "email", "created_at"),
        Index("ix_login_attempts_ip_created", "ip", "created_at"),
        Index("ix_login_attempts_user_created", "user_id", "created_at"),
    )
