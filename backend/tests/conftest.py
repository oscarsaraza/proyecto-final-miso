"""Fixtures comunes para pruebas del backend."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db_session
from app.modules.identity.service import insured_auth_service
from app.modules.auth.service import auth_service
from app.modules.profile.service import profile_service


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
    insured_auth_service.reset_state()
    profile_service.clear()
    yield
    insured_auth_service.reset_state()
    profile_service.clear()


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
async def postgres_session():
    """PostgreSQL real en la base solventa_test, con las tablas recreadas; la API lo usa en lugar del doble."""
    test_url = make_url(settings.DATABASE_URL).set(database="solventa_test")
    admin = create_async_engine(test_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        if not await conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = 'solventa_test'")):
            await conn.execute(text("CREATE DATABASE solventa_test"))
    await admin.dispose()

    engine = create_async_engine(test_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def override_db():
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db
    async with sessions() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def async_client():
    """Cliente HTTP asíncrono para pruebas de integración de FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
