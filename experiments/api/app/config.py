from functools import lru_cache

from pydantic_settings import BaseSettings


class Opciones(BaseSettings):
    provider_url: str = "http://provider-sim:8001"
    provider_timeout_ms: int = 700
    cache_ttl_s: float = 60.0
    replica_name: str = "unknown"
    cb_fallos: int = 3
    cb_ventana_s: float = 10.0

    @property
    def timeout_segundos(self) -> float:
        return self.provider_timeout_ms / 1000


@lru_cache
def obtener_opciones() -> Opciones:
    return Opciones()
