import httpx

from app.cotizacion.cache import CachePerfiles
from app.cotizacion.circuito import Circuito
from app.cotizacion.open_finance import ProveedorOpenFinance
from app.cotizacion.perfil import Perfil, perfil_materializado
from app.cotizacion.rating import calcular_prima
from app.cotizacion.schemas import RespuestaCotizacion, SolicitudCotizacion

ORIGEN_CACHE = "cache"
ORIGEN_PROVEEDOR = "open-finance"
ORIGEN_MATERIALIZADO = "perfil-materializado"


class ServicioCotizacion:
    """Degrada la fuente del perfil antes que rechazar la solicitud."""

    def __init__(
        self,
        cache: CachePerfiles,
        proveedor: ProveedorOpenFinance,
        circuito: Circuito,
        replica: str,
    ) -> None:
        self.cache = cache
        self.proveedor = proveedor
        self.circuito = circuito
        self.replica = replica

    async def cotizar(self, solicitud: SolicitudCotizacion) -> RespuestaCotizacion:
        perfil, origen = await self.resolver_perfil(solicitud.cliente_id)
        return RespuestaCotizacion(
            status="degraded" if origen == ORIGEN_MATERIALIZADO else "ok",
            origen_perfil=origen,
            circuito="abierto" if self.circuito.abierto() else "cerrado",
            replica=self.replica,
            prima=calcular_prima(solicitud.monto, solicitud.edad, perfil.score),
            nivel_riesgo=perfil.nivel,
        )

    async def resolver_perfil(self, cliente_id: str) -> tuple[Perfil, str]:
        """Recorre las fuentes de la más barata a la más costosa."""
        en_cache = self.cache.obtener(cliente_id)
        if en_cache is not None:
            return en_cache, ORIGEN_CACHE

        if self.circuito.abierto():
            return perfil_materializado(cliente_id), ORIGEN_MATERIALIZADO

        try:
            perfil = await self.proveedor.obtener(cliente_id)
        except httpx.HTTPError:
            self.circuito.registrar_fallo()
            return perfil_materializado(cliente_id), ORIGEN_MATERIALIZADO

        self.cache.guardar(cliente_id, perfil)
        self.circuito.registrar_exito()
        return perfil, ORIGEN_PROVEEDOR
