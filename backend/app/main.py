"""Punto de entrada principal del backend monolito modular de Solventa."""
from datetime import datetime, timezone
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import TenantContextMiddleware
from app.bff.experience.router import router as experience_router
from app.bff.quote_edge.router import router as quote_edge_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend Monolito Modular API-First para Solventa Seguros Digitales",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 1. Configuración de CORS para canal Web y socios
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Bienvenido a {settings.PROJECT_NAME}",
        "docs": "/docs",
        "health": "/health",
    }
