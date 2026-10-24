"""Router BFF para socios B2B (quote-edge) con aislamiento multi-tenant y credenciales OAuth2 (HU-WEB-10, HU-WEB-11)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.idempotency import find_response, save_response, IdempotencyConflictError
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
    summary="Emitir token JWT de socio B2B (OAuth2 Client Credentials)",
    responses={
        status.HTTP_200_OK: {
            "description": "Token JWT emitido exitosamente con claims de confinamiento del socio.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Credenciales inválidas o socio con credenciales revocadas (auditable en CloudWatch).",
        },
    },
)
async def issue_partner_token(
    request: PartnerTokenRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Autentica un socio de distribución mediante `client_id` y `client_secret` (OAuth2 *Client Credentials*)
    y retorna un token JWT firmado con `role: "partner"` y el `partner_id` asignado (**HU-WEB-10**).
    """
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
    summary="Generar cotización desde el canal del socio B2B",
    responses={
        status.HTTP_200_OK: {
            "description": "Cotización calculada, guardada bajo el partner_id del socio y con cuota de uso (quota_used) incrementada.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Encabezado Idempotency-Key ausente o vacío (HU-WEB-11).",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Token ausente, expirado, inválido, de otro rol o de un socio revocado.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "La clave de idempotencia ya fue utilizada con una solicitud de cotización diferente (HU-WEB-11).",
        },
    },
)
async def create_partner_quote(
    request: QuoteRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    simulated_delay: float = 0.0,
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Calcula y registra una cotización B2B confinada al `partner_id` derivado del token JWT del socio
    autenticado e incrementa su contador `quota_used` (**HU-WEB-10**).
    Garantiza idempotencia por socio y clave: si la misma clave y payload se reenvían,
    retorna la cotización previa sin duplicar registros en base de datos (**HU-WEB-11**).
    """
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El encabezado 'Idempotency-Key' es obligatorio para cotizaciones B2B.",
        )

    cleaned_key = idempotency_key.strip()
    try:
        saved = await find_response(
            session=db,
            partner_id=current_partner.partner_id,
            idempotency_key=cleaned_key,
            request=request,
        )
    except IdempotencyConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de idempotencia: la clave ya fue utilizada con una solicitud diferente.",
        )

    if saved:
        return PartnerQuoteResponse(
            **saved.response_body,
            partner_id=current_partner.partner_id,
        )

    quote = await rating_service.create_quote(
        session=db,
        request=request,
        simulated_bureau_delay=simulated_delay,
        partner_id=current_partner.partner_id,
        commit=False,
    )
    response = PartnerQuoteResponse(
        **quote.model_dump(),
        partner_id=current_partner.partner_id,
    )
    save_response(
        session=db,
        partner_id=current_partner.partner_id,
        idempotency_key=cleaned_key,
        request=request,
        status=status.HTTP_200_OK,
        body=response.model_dump(mode="json"),
    )
    await db.commit()
    return response


@router.get(
    "/quotes/{quote_id}",
    response_model=PartnerQuoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar cotización individual del socio B2B",
    responses={
        status.HTTP_200_OK: {
            "description": "Detalle de la cotización perteneciente al socio autenticado.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Token de socio ausente, inválido o revocado.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "La cotización no existe o pertenece a otro socio / canal (aislamiento multi-tenant).",
        },
    },
)
async def get_partner_quote(
    quote_id: str,
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Consulta el detalle de una cotización propia del socio autenticado; retorna `404 Not Found`
    si no existe o si pertenece a otro socio o al canal comercial interno (**HU-WEB-10**).
    """
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
    summary="Listar histórico de cotizaciones del socio B2B",
    responses={
        status.HTTP_200_OK: {
            "description": "Listado de cotizaciones confinado exclusivamente al socio autenticado.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Token de socio ausente, inválido o revocado.",
        },
    },
)
async def list_partner_quotes(
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Consulta el listado histórico de cotizaciones generadas exclusivamente por el socio autenticado,
    ordenadas desde la más reciente (**HU-WEB-10**).
    """
    return await rating_service.list_partner_quotes(
        session=db,
        partner_id=current_partner.partner_id,
    )


