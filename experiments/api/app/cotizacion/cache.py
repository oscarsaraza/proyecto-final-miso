import time

from app.cotizacion.perfil import Perfil


class CachePerfiles:
    def __init__(self, ttl_segundos: float) -> None:
        self.ttl_segundos = ttl_segundos
        self.entradas: dict[str, tuple[float, Perfil]] = {}

    def obtener(self, cliente_id: str) -> Perfil | None:
        entrada = self.entradas.get(cliente_id)
        if entrada and time.monotonic() - entrada[0] < self.ttl_segundos:
            return entrada[1]
        return None

    def guardar(self, cliente_id: str, perfil: Perfil) -> None:
        self.entradas[cliente_id] = (time.monotonic(), perfil)
