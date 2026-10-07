"""Router BFF para canales Web y Móvil (experience-edge) - Placeholders para Sprint 1."""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, Field

from app.modules.profile.models import ClientIdentification, ConsentRequest, ConsentRecord
from app.modules.profile.service import profile_service
from app.modules.rating.models import QuoteRequest, QuoteResponse
from app.modules.rating.service import rating_service
from app.modules.policy.models import PolicyIssueRequest, PolicyRecord
from app.modules.policy.service import policy_service
from app.modules.payments.models import PaymentChargeRequest, PaymentReceipt
from app.modules.payments.service import payment_service

router = APIRouter(prefix="/experience", tags=["Experience BFF"])


class LoginRequest(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "asesor.demo@solventa.com"})
    password: str = Field(..., json_schema_extra={"example": "SuperSecret2026!"})
    totp_code: str = Field(..., json_schema_extra={"example": "123456"})


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    advisor_name: str


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login con 2FA y bloqueo de intentos (Placeholder para HU-WEB-13)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Autenticación con 2FA pendiente de implementación en HU-WEB-13.",
    )


@router.post("/clients/validate", response_model=Dict[str, Any])
async def validate_client(client: ClientIdentification):
    """Valida la asegurabilidad sociodemográfica del tomador (Placeholder para HU-WEB-02)."""
    try:
        profile_service.validate_insurable_age(client)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))
    return {"status": "ELIGIBLE"}


@router.post("/consent", response_model=ConsentRecord)
async def submit_consent(consent: ConsentRequest):
    """Registra consentimiento auditable de Open Finance (Placeholder para HU-WEB-01)."""
    try:
        return profile_service.register_consent(consent)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))


@router.post("/quotes", response_model=QuoteResponse)
async def create_quote(
    request: QuoteRequest,
    simulated_delay: float = 0.0,
):
    """Calcula la cotización en memoria con fallback protector (Placeholder para HU-WEB-03 y HU-WEB-04)."""
    try:
        return await rating_service.calculate_quote(request, simulated_bureau_delay=simulated_delay)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))


@router.post("/policies", response_model=PolicyRecord)
async def issue_policy(request: PolicyIssueRequest):
    """Emite la póliza contractual y genera evento outbox (Placeholder para HU-WEB-05)."""
    try:
        return policy_service.issue_policy(request)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))


@router.post("/payments/charge", response_model=PaymentReceipt)
async def charge_premium(
    request: PaymentChargeRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """Cobra la prima con garantía de idempotencia (Placeholder para HU-WEB-06)."""
    try:
        return payment_service.process_charge(request, idempotency_key=idempotency_key or "")
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))
