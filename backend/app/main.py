"""Punto de entrada principal del backend monolito modular de Solventa."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.middleware import TenantContextMiddleware
from app.bff.experience.router import router as experience_router
from app.bff.quote_edge.router import router as quote_edge_router
from app.bff.auth.router import router as auth_router
from app.modules.auth.models import UserDB  # noqa: F401 - registrar tablas en Base.metadata
from app.modules.rating.models import PartnerDB, QuoteDB  # noqa: F401 - registrar tablas en Base.metadata
from app.modules.policy.models import PolicyDB  # noqa: F401 - registrar tablas en Base.metadata
from app.core.outbox import OutboxMessageDB  # noqa: F401 - registrar tablas en Base.metadata
from app.core.idempotency import IdempotencyRecordDB  # noqa: F401 - registrar tablas en Base.metadata
from app.modules.payments.models import PaymentTransactionDB  # noqa: F401 - registrar tablas en Base.metadata
from app.modules.profile.models import FinancialEntityDB, CityDB  # noqa: F401 - registrar tablas en Base.metadata
from app.modules.identity import db_models as identity_db_models  # noqa: F401 - registrar tablas en Base.metadata
from app.modules.auth.service import auth_service
from app.modules.profile.service import profile_service
from app.modules.rating.service import rating_service
from app.modules.identity.service import insured_auth_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización de tablas relacionales, usuario asesor y socios B2B semilla (HU-WEB-13, HU-WEB-10)."""
    insured_auth_service.sms  # falla al arrancar si la configuración del SMS está incompleta
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS partner_id VARCHAR(64)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_quotes_partner_id ON quotes (partner_id)"))
        async with AsyncSessionLocal() as session:
            if settings.debug_enabled:
                await auth_service.seed_default_users(session)
            await profile_service.seed_default_catalogs(session)
            await rating_service.seed_default_partners(session)
            await insured_auth_service.seed_default_account(session)
    except Exception as exc:
        print(f"Aviso de inicialización de base de datos en arranque: {exc}")
    yield


def docs_urls(enabled: bool) -> dict:
    """Rutas de la documentación interactiva; apagadas cuando ENVIRONMENT es production."""
    if not enabled:
        return {"docs_url": None, "redoc_url": None, "openapi_url": None}
    return {"docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend Monolito Modular API-First para Solventa Seguros Digitales",
    lifespan=lifespan,
    **docs_urls(settings.debug_enabled),
)

# 1. CORS: solo los orígenes de CORS_ORIGINS; el portal y la API comparten origen detrás de CloudFront
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)

# 2. Middleware de Contexto Multi-Tenant (ASR-06 / HA-14)
app.add_middleware(TenantContextMiddleware)

# 3. Endpoint de Sondeo de Salud para AWS ALB (HA-09: cada 5s, umbral 2)
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """Endpoint consultado activamente por el ALB de AWS para determinar nodos sanos."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# 4. Registro de Routers BFF
app.include_router(experience_router, prefix=settings.API_V1_STR)
app.include_router(quote_edge_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Bienvenido a {settings.PROJECT_NAME}",
        "docs": "/docs" if settings.debug_enabled else None,
        "health": "/health",
    }
