"""Fixtures comunes para pruebas del backend."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db_session
from app.core.middleware import idempotency_store
from app.modules.identity.service import insured_auth_service
from app.modules.auth.service import auth_service


class InMemorySessionTestDouble:
    """Test Double asíncrono en memoria para emular sesiones de base de datos en pruebas."""

    def __init__(self):
        self.users = {}

    async def execute(self, stmt):
        class Result:
            def __init__(self, items):
                self._items = items

            def scalars(self):
                class Scalars:
                    def __init__(self, items):
                        self._items = items

                    def first(self):
                        return self._items[0] if self._items else None

                return Scalars(self._items)

        clean_username = stmt.whereclause.right.value
        user = self.users.get(clean_username)
        return Result([user] if user else [])

    def add(self, user):
        self.users[user.username] = user

    async def commit(self):
        pass

    async def refresh(self, user):
        pass


@pytest.fixture(autouse=True)
def clean_stores():
    """Limpia los estados en memoria antes de cada test."""
    idempotency_store.clear()
    insured_auth_service.reset_state()
    yield
    idempotency_store.clear()
    insured_auth_service.reset_state()


@pytest.fixture(autouse=True)
async def test_db_session():
    """Configura base de datos en memoria para aislar pruebas sin requerir daemon de PostgreSQL."""
    session = InMemorySessionTestDouble()
    await auth_service.seed_default_users(session)

    async def override_db():
        yield session

    app.dependency_overrides[get_db_session] = override_db
    yield session
    app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
async def async_client():
    """Cliente HTTP asíncrono para pruebas de integración de FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
