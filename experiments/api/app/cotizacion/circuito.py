import time


class Circuito:
    """Descarta al proveedor tras una racha de fallos, para no pagar el timeout en cada solicitud."""

    def __init__(self, fallos_para_abrir: int, ventana_segundos: float) -> None:
        self.fallos_para_abrir = fallos_para_abrir
        self.ventana_segundos = ventana_segundos
        self.fallos = 0
        self.abierto_hasta = 0.0

    def abierto(self) -> bool:
        return time.monotonic() < self.abierto_hasta

    def registrar_fallo(self) -> None:
        self.fallos += 1
        if self.fallos >= self.fallos_para_abrir:
            self.abierto_hasta = time.monotonic() + self.ventana_segundos

    def registrar_exito(self) -> None:
        self.fallos = 0
        self.abierto_hasta = 0.0
