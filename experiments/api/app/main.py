"""Prototipo de la API de cotización que sostiene los experimentos E1 y E3."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app import health
from app.config import obtener_opciones
from app.cotizacion.cache import CachePerfiles
from app.cotizacion.circuito import Circuito
from app.cotizacion.open_finance import ProveedorOpenFinance
from app.cotizacion.router import router as router_cotizacion
from app.cotizacion.service import ServicioCotizacion


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    opciones = obtener_opciones()
    async with httpx.AsyncClient(timeout=opciones.timeout_segundos) as cliente:
        app.state.servicio_cotizacion = ServicioCotizacion(
            cache=CachePerfiles(opciones.cache_ttl_s),
            proveedor=ProveedorOpenFinance(cliente, opciones.provider_url),
            circuito=Circuito(opciones.cb_fallos, opciones.cb_ventana_s),
            replica=opciones.replica_name,
        )
        yield


app = FastAPI(title="Solventa · API de cotización", lifespan=ciclo_de_vida)
app.include_router(health.router)
app.include_router(router_cotizacion)
