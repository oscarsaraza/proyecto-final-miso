"""Fixtures comunes para pruebas del backend."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.middleware import idempotency_store
from app.modules.identity.service import insured_auth_service


@pytest.fixture(autouse=True)
def clean_stores():
    """Limpia los estados en memoria antes de cada test."""
    idempotency_store.clear()
    insured_auth_service.reset_state()
    yield
    idempotency_store.clear()
    insured_auth_service.reset_state()


@pytest.fixture
async def async_client():
    """Cliente HTTP asíncrono para pruebas de integración de FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
