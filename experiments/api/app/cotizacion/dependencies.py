from typing import Annotated

from fastapi import Depends, Request

from app.cotizacion.service import ServicioCotizacion


def obtener_servicio(request: Request) -> ServicioCotizacion:
    return request.app.state.servicio_cotizacion


ServicioCotizacionDep = Annotated[ServicioCotizacion, Depends(obtener_servicio)]
