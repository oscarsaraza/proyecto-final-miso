"""Router BFF para socios B2B (quote-edge) con aislamiento multi-tenant y credenciales OAuth2 (HU-WEB-10)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import (
    authenticate_partner,
    create_partner_access_token,
    get_current_partner,
)
from app.modules.rating.models import (
    PartnerDB,
    PartnerQuoteResponse,
    PartnerTokenRequest,
    PartnerTokenResponse,
    QuoteRequest,
)
from app.modules.rating.service import rating_service

router = APIRouter(prefix="/quote-edge", tags=["Quote Edge B2B"])


@router.post(
    "/auth/token",
    response_model=PartnerTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def issue_partner_token(
    request: PartnerTokenRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Emite un token JWT para un socio B2B mediante el flujo OAuth2 Client Credentials (HU-WEB-10)."""
    partner = await authenticate_partner(
        session=db,
        client_id=request.client_id,
        client_secret=request.client_secret,
    )
    access_token = create_partner_access_token(
        client_id=partner.client_id,
        partner_id=partner.partner_id,
    )
    return PartnerTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.PARTNER_TOKEN_EXPIRE_MINUTES * 60,
        partner_id=partner.partner_id,
    )


@router.post(
    "/quotes",
    response_model=PartnerQuoteResponse,
    status_code=status.HTTP_200_OK,
)
async def create_partner_quote(
    request: QuoteRequest,
    simulated_delay: float = 0.0,
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """Calcula y registra una cotización B2B confinada al socio autenticado e incrementa su cuota (HU-WEB-10)."""
    quote = await rating_service.create_quote(
        session=db,
        request=request,
        simulated_bureau_delay=simulated_delay,
        partner_id=current_partner.partner_id,
    )
    return PartnerQuoteResponse(
        **quote.model_dump(),
        partner_id=current_partner.partner_id,
    )


@router.get(
    "/quotes/{quote_id}",
    response_model=PartnerQuoteResponse,
    status_code=status.HTTP_200_OK,
)
async def get_partner_quote(
    quote_id: str,
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """Consulta el detalle de una cotización propia del socio autenticado; retorna 404 si no existe o es de otro socio (HU-WEB-10)."""
    quote = await rating_service.get_partner_quote(
        session=db,
        quote_id=quote_id,
        partner_id=current_partner.partner_id,
    )
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada",
        )
    return quote


@router.get(
    "/quotes",
    response_model=List[PartnerQuoteResponse],
    status_code=status.HTTP_200_OK,
)
async def list_partner_quotes(
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """Consulta el listado histórico de cotizaciones generadas exclusivamente por el socio autenticado (HU-WEB-10)."""
    return await rating_service.list_partner_quotes(
        session=db,
        partner_id=current_partner.partner_id,
    )


