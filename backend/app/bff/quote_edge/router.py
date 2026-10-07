"""Router BFF para socios B2B (quote-edge) con aislamiento multi-tenant (Placeholder)."""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status
from app.modules.rating.models import QuoteRequest, QuoteResponse
from app.modules.rating.service import rating_service

router = APIRouter(prefix="/quote-edge", tags=["Quote Edge B2B"])


@router.post("/quotes", response_model=QuoteResponse)
async def create_partner_quote(
    request: QuoteRequest,
    x_partner_id: Optional[str] = Header(None, alias="X-Partner-Id"),
):
    """Endpoint de cotización B2B con validación obligatoria de socio (Placeholder para Sprint 2)."""
    if not x_partner_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cabecera 'X-Partner-Id' es obligatoria para acceder al canal de socios B2B.",
        )
    try:
        return await rating_service.calculate_quote(request)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))
