"""Middleware y variable de contexto para multi-tenancy."""
import json
from contextvars import ContextVar
from typing import Optional
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

