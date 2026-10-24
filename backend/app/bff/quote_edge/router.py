"""Router BFF para socios B2B (quote-edge) con aislamiento multi-tenant y credenciales OAuth2 (HU-WEB-10, HU-WEB-14)."""
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
from app.modules.policy.models import (
    PartnerPolicyIssueRequest,
    PartnerPolicyResponse,
)
from app.modules.policy.service import (
    QuoteExpiredError,
    QuoteNotFoundError,
    policy_service,
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


# -- Cotizaciones B2B (HU-WEB-10) --------------------------------------------------------------


@router.post(
    "/quotes",
    response_model=PartnerQuoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar cotización desde el canal del socio B2B",
    responses={
        status.HTTP_200_OK: {
            "description": "Cotización calculada, guardada bajo el partner_id del socio y con cuota de uso (quota_used) incrementada.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Token ausente, expirado, inválido, de otro rol o de un socio revocado.",
        },
    },
)
async def create_partner_quote(
    request: QuoteRequest,
    simulated_delay: float = 0.0,
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Calcula y registra una cotización B2B confinada al `partner_id` derivado del token JWT del socio
    autenticado e incrementa su contador `quota_used` (**HU-WEB-10**).
    """
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


# -- Emisión y Consulta de Pólizas B2B (HU-WEB-14) ----------------------------------------------


@router.post(
    "/policies",
    response_model=PartnerPolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Emitir póliza digital desde el canal del socio B2B",
    responses={
        status.HTTP_200_OK: {
            "description": "Póliza emitida exitosamente e idempotente ante reintentos (HU-WEB-14).",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Token ausente, inválido, expirado o de socio revocado.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Cotización inexistente o perteneciente a otro socio / canal (aislamiento multi-tenant).",
        },
        status.HTTP_409_CONFLICT: {
            "description": "La cotización ha expirado y no puede ser emitida.",
        },
    },
)
async def issue_partner_policy(
    request: PartnerPolicyIssueRequest,
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Emite una póliza de seguro formalizada a partir de un `quote_id` vigente y perteneciente al socio autenticado (**HU-WEB-14**).
    Garantiza atomicidad e idempotencia estricta (**HA-11**) y aislamiento multi-tenant (**HA-14**).
    """
    try:
        return await policy_service.issue_partner_policy(
            session=db,
            request=request,
            partner_id=current_partner.partner_id,
        )
    except QuoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada",
        )
    except QuoteExpiredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La cotización ha expirado; debe calcular una nueva para emitir",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/policies/{policy_number}",
    response_model=PartnerPolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar póliza individual del socio B2B",
    responses={
        status.HTTP_200_OK: {
            "description": "Detalle de la póliza emitida perteneciente al socio autenticado.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Token de socio ausente, inválido o revocado.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "La póliza no existe o pertenece a otro socio (aislamiento multi-tenant).",
        },
    },
)
async def get_partner_policy(
    policy_number: str,
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Consulta el detalle de una póliza propia del socio autenticado; retorna `404 Not Found`
    si no existe o si pertenece a otro socio (**HU-WEB-14**, **HA-14**).
    """
    policy = await policy_service.get_partner_policy(
        session=db,
        policy_number=policy_number,
        partner_id=current_partner.partner_id,
    )
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Póliza no encontrada",
        )
    return policy


@router.get(
    "/policies",
    response_model=List[PartnerPolicyResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar histórico de pólizas del socio B2B (CQRS)",
    responses={
        status.HTTP_200_OK: {
            "description": "Listado de pólizas emitidas confinado exclusivamente al socio autenticado.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Token de socio ausente, inválido o revocado.",
        },
    },
)
async def list_partner_policies(
    current_partner: PartnerDB = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Consulta el listado histórico de pólizas emitidas por el socio autenticado mediante
    la vista de lectura optimizada CQRS (**HU-WEB-14**, **HA-04**).
    """
    return await policy_service.list_partner_policies(
        session=db,
        partner_id=current_partner.partner_id,
    )
