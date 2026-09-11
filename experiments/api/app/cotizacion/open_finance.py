import httpx

from app.cotizacion.perfil import Perfil


class ProveedorOpenFinance:
    def __init__(self, cliente: httpx.AsyncClient, url_base: str) -> None:
        self.cliente = cliente
        self.url_base = url_base

    async def obtener(self, cliente_id: str) -> Perfil:
        """Propaga httpx.HTTPError si el proveedor falla o agota el presupuesto de espera."""
        respuesta = await self.cliente.get(f"{self.url_base}/profile/{cliente_id}")
        respuesta.raise_for_status()
        datos = respuesta.json()
        return Perfil(score=datos["score"], nivel=datos["nivel"])
