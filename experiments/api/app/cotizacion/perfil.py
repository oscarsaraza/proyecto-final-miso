from dataclasses import dataclass


@dataclass(frozen=True)
class Perfil:
    score: int
    nivel: str


PERFILES_MATERIALIZADOS = {
    "CLI-001": Perfil(score=720, nivel="bajo"),
    "CLI-002": Perfil(score=640, nivel="medio"),
    "CLI-003": Perfil(score=580, nivel="alto"),
}
PERFIL_POR_DEFECTO = Perfil(score=600, nivel="medio")


def perfil_materializado(cliente_id: str) -> Perfil:
    """Respaldo local que sostiene la cotización cuando el proveedor externo no responde."""
    return PERFILES_MATERIALIZADOS.get(cliente_id, PERFIL_POR_DEFECTO)
