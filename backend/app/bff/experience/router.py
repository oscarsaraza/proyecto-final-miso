"""Router BFF para canales Web y Móvil (experience-edge) (HU-WEB-13)."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.idempotency import IdempotencyConflictError
from app.core.security import require_roles
from app.modules.auth.models import LoginRequest, LoginResponse, RefreshTokenRequest
from app.modules.auth.service import auth_service
from app.modules.profile.models import ClientIdentification, ConsentRequest, ConsentRecord
from app.modules.profile.service import profile_service
from app.modules.rating.models import QuoteRequest, QuoteResponse
from app.modules.rating.service import rating_service
from app.modules.policy.models import PolicyIssueRequest, PolicyRecord
from app.modules.policy.service import PolicyNotFoundError, QuoteExpiredError, QuoteNotFoundError, policy_service
from app.modules.payments.models import PaymentChargeRequest, PaymentReceipt
from app.modules.payments.gateway import GatewayUnavailableError
from app.modules.payments.service import (
    AmountMismatchError,
    PaymentDeclinedError,
    PolicyAlreadyPaidError,
    payment_service,
)

router = APIRouter(prefix="/experience", tags=["Experience BFF"])


@router.post("/auth/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Inicio de sesión corporativo con 2FA TOTP y bloqueo tras 3 intentos (HU-WEB-13)."""
    user = await auth_service.authenticate_user(
        session=db,
        username=request.username,
        password=request.password,
        totp_code=request.totp_code,
    )
    return auth_service.generate_session_tokens(user)


@router.post("/auth/refresh", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Renovación silenciosa de sesión JWT mediante refresh token (HU-WEB-13)."""
    return await auth_service.refresh_session(
        session=db,
        refresh_token=request.refresh_token,
    )


@router.post(
    "/clients/validate",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_roles(["advisor"]))],
)
async def validate_client(client: ClientIdentification):
    """Valida la asegurabilidad sociodemográfica del tomador (Placeholder para HU-WEB-02)."""
    try:
        profile_service.validate_insurable_age(client)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))
    return {"status": "ELIGIBLE"}


@router.post(
    "/consent",
    response_model=ConsentRecord,
    dependencies=[Depends(require_roles(["advisor"]))],
)
async def submit_consent(consent: ConsentRequest):
    """Registra consentimiento auditable de Open Finance (Placeholder para HU-WEB-01)."""
    try:
        return profile_service.register_consent(consent)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))


@router.post(
    "/quotes",
    response_model=QuoteResponse,
    dependencies=[Depends(require_roles(["advisor"]))],
)
async def create_quote(
    request: QuoteRequest,
    simulated_delay: float = 0.0,
    db: AsyncSession = Depends(get_db_session),
):
    """Calcula y guarda la cotización; si el buró supera el timeout, la entrega degradada con perfil parcial."""
    try:
        return await rating_service.create_quote(db, request, simulated_bureau_delay=simulated_delay)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))


@router.post(
    "/policies",
    response_model=PolicyRecord,
    dependencies=[Depends(require_roles(["advisor"]))],
)
async def issue_policy(
    request: PolicyIssueRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Emite la póliza de una cotización vigente; repetir la emisión devuelve la misma póliza (HU-WEB-05)."""
    try:
        return await policy_service.issue_policy(db, request)
    except QuoteNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La cotización no existe.")
    except QuoteExpiredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La cotización venció: recalcule la tarifa con datos actuales.",
        )


# Respuesta de cada error del cobro; el rechazo trae su motivo en la excepción.
PAYMENT_ERRORS = {
    PolicyNotFoundError: (status.HTTP_404_NOT_FOUND, "La póliza no existe."),
    AmountMismatchError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "El monto no coincide con la prima de la póliza."),
    PolicyAlreadyPaidError: (status.HTTP_409_CONFLICT, "La póliza ya está pagada."),
    IdempotencyConflictError: (status.HTTP_409_CONFLICT, "La clave de idempotencia ya se usó con otra solicitud."),
    PaymentDeclinedError: (status.HTTP_402_PAYMENT_REQUIRED, None),
    GatewayUnavailableError: (
        status.HTTP_502_BAD_GATEWAY, "La pasarela no respondió. Reintente con la misma clave: no se cobrará dos veces."
    ),
}


@router.post(
    "/payments/charge",
    response_model=PaymentReceipt,
    dependencies=[Depends(require_roles(["advisor"]))],
)
async def charge_premium(
    request: PaymentChargeRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
    db: AsyncSession = Depends(get_db_session),
):
    """Cobra la prima una sola vez; reintentar con la misma clave repite la respuesta sin otro cargo (HU-WEB-06)."""
    try:
        return await payment_service.process_charge(db, request, idempotency_key)
    except tuple(PAYMENT_ERRORS) as exc:
        status_code, detail = PAYMENT_ERRORS[type(exc)]
        raise HTTPException(status_code=status_code, detail=detail or str(exc))
