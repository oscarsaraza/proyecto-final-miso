from fastapi import APIRouter

from app.cotizacion.dependencies import ServicioCotizacionDep
from app.cotizacion.schemas import RespuestaCotizacion, SolicitudCotizacion

router = APIRouter(prefix="/api/v1", tags=["cotizacion"])


@router.post("/quotes", response_model=RespuestaCotizacion)
async def cotizar(
    solicitud: SolicitudCotizacion, servicio: ServicioCotizacionDep
) -> RespuestaCotizacion:
    return await servicio.cotizar(solicitud)
