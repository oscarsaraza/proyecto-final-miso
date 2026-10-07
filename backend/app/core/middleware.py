"""Middlewares y variables de contexto para multi-tenancy e idempotencia."""
import hashlib
import json
from contextvars import ContextVar
from typing import Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

# ContextVar segura para aislamiento multi-tenant en peticiones asíncronas (ASR-06 / HA-14)
tenant_context: ContextVar[Optional[str]] = ContextVar("tenant_context", default=None)


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        partner_id = request.headers.get("X-Partner-Id")
        token = tenant_context.set(partner_id)
        try:
            response = await call_next(request)
            return response
        finally:
            tenant_context.reset(token)


class InMemoryIdempotencyStore:
    """Almacén de idempotencia (en memoria para dev/tests, mapeado a tabla idempotency_records en PostgreSQL)."""

    def __init__(self):
        self._records: Dict[str, Dict[str, Any]] = {}

    def _make_key(self, partner_id: Optional[str], idempotency_key: str) -> str:
        return f"{partner_id or 'default'}:{idempotency_key}"

    def compute_hash(self, body: bytes) -> str:
        return hashlib.sha256(body).hexdigest()

    def get(self, partner_id: Optional[str], idempotency_key: str) -> Optional[Dict[str, Any]]:
        key = self._make_key(partner_id, idempotency_key)
        return self._records.get(key)

    def save(
        self,
        partner_id: Optional[str],
        idempotency_key: str,
        request_hash: str,
        status_code: int,
        response_body: Any,
    ) -> None:
        key = self._make_key(partner_id, idempotency_key)
        self._records[key] = {
            "request_hash": request_hash,
            "status_code": status_code,
            "response_body": response_body,
        }

    def clear(self) -> None:
        self._records.clear()


idempotency_store = InMemoryIdempotencyStore()
