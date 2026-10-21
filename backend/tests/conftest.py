"""Fixtures comunes para pruebas del backend."""
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db_session
from app.core.sms import ConsoleSmsSender, SmsDeliveryError
from app.modules.identity.service import InsuredAuthService, insured_auth_service
from app.modules.auth.service import auth_service
from app.modules.profile.service import profile_service


class InMemorySessionTestDouble:
    """Test Double asíncrono en memoria para emular sesiones de base de datos en pruebas."""

    def __init__(self):
        self.users = {}
        self.financial_entities = {}
        self.cities = {}

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

                    def all(self):
                        return list(self._items)

                return Scalars(self._items)

        sql_str = str(stmt).lower()
        if "financial_entities" in sql_str:
            if "financial_entities.code" in sql_str and "financial_entities.name" not in sql_str:
                return Result(list(self.financial_entities.keys()))
            entities = sorted(self.financial_entities.values(), key=lambda x: getattr(x, "name", ""))
            return Result(entities)

        if "cities" in sql_str:
            if "cities.code" in sql_str and "cities.name" not in sql_str:
                return Result(list(self.cities.keys()))
            cities = sorted(self.cities.values(), key=lambda x: getattr(x, "name", ""))
            return Result(cities)

        try:
            clean_username = stmt.whereclause.right.value
            user = self.users.get(clean_username)
            return Result([user] if user else [])
        except Exception:
            return Result([])

    def add(self, obj):
        from app.modules.profile.models import FinancialEntityDB, CityDB

        if isinstance(obj, FinancialEntityDB):
            if not getattr(obj, "id", None):
                obj.id = len(self.financial_entities) + 1
            self.financial_entities[obj.code] = obj
        elif isinstance(obj, CityDB):
            if not getattr(obj, "id", None):
                obj.id = len(self.cities) + 1
            self.cities[obj.code] = obj
        else:
            self.users[obj.username] = obj

    async def commit(self):
        pass

    async def refresh(self, user):
        pass


@pytest.fixture(autouse=True)
def sms_simulado(monkeypatch):
    """Las pruebas nunca envían SMS reales, aunque el .env local tenga Twilio."""
    monkeypatch.setattr(insured_auth_service, "_sms", ConsoleSmsSender())


@pytest.fixture(autouse=True)
def clean_stores():
    """Limpia los estados en memoria antes de cada test."""
    profile_service.clear()
    yield
    profile_service.clear()


@pytest.fixture(autouse=True)
async def test_db_session():
    """Configura base de datos en memoria para aislar pruebas sin requerir daemon de PostgreSQL."""
    session = InMemorySessionTestDouble()
    await auth_service.seed_default_users(session)
    await profile_service.seed_default_catalogs(session)

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


INSURED_EMAIL = "maria.ruiz@correo.co"
INSURED_PASSWORD = "Solventa2026!"
INSURED_PHONE = "+573001112233"


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, delta: timedelta):
        self.now += delta


class RecordingSmsSender:
    exposes_code = True

    def __init__(self):
        self.sent = []
        self.fail = False

    async def send(self, to: str, body: str) -> None:
        if self.fail:
            raise SmsDeliveryError("caído")
        self.sent.append((to, body))


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def sms():
    return RecordingSmsSender()


@pytest.fixture
async def identity(postgres_session, clock, sms):
    """Servicio de identidad sobre PostgreSQL real con reloj y SMS falsos, y María registrada."""
    service = InsuredAuthService(clock=clock, sms_sender=sms)
    await service.register(
        postgres_session,
        user_id="ins-0001",
        email=INSURED_EMAIL,
        full_name="María Ruiz",
        document_number="1020304050",
        phone=INSURED_PHONE,
        password=INSURED_PASSWORD,
    )
    return service


@pytest.fixture
async def seeded_insured(postgres_session):
    """María registrada para las pruebas de la API, que usan el servicio global."""
    await insured_auth_service.register(
        postgres_session,
        user_id="ins-0001",
        email=INSURED_EMAIL,
        full_name="María Ruiz",
        document_number="1020304050",
        phone=INSURED_PHONE,
        password=INSURED_PASSWORD,
    )
