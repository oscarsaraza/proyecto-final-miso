"""Transactional outbox: eventos de dominio guardados en la misma transacción que su agregado (ASR-05)."""
import uuid
from sqlalchemy import JSON, Column, DateTime, String, func
from app.core.database import Base


class OutboxMessageDB(Base):
    """Evento pendiente de publicar hacia SQS; lo escribe el módulo dueño del agregado al confirmar su cambio."""
    __tablename__ = "outbox"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_id = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(16), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
