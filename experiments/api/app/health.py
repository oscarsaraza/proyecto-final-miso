from fastapi import APIRouter

from app.config import obtener_opciones

router = APIRouter(tags=["operacion"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"estado": "vivo", "replica": obtener_opciones().replica_name}
