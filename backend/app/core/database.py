"""Gestión de sesiones asíncronas con SQLAlchemy y PostgreSQL 16."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

Base = declarative_base()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session():
    """Generador de sesión de base de datos para inyección de dependencias."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
