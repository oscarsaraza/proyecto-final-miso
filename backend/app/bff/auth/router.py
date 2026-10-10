"""Router BFF de autenticación del asegurado para la app móvil (HU-MOV-02, HU-MOV-12)."""
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.modules.identity.models import InsuredLoginRequest, OtpRequest, OtpResponse, TokenPair
from app.modules.identity.service import (
    OTP_TTL,
    AccountLockedError,
    InvalidCredentialsError,
    insured_auth_service,
)

router = APIRouter(prefix="/auth", tags=["Auth Asegurado"])


@router.post("/otp", response_model=OtpResponse)
async def request_otp(request: OtpRequest):
    code = insured_auth_service.request_otp(request.email)
    return OtpResponse(
        message="Si el correo está registrado, enviamos un código por SMS.",
        expires_in=int(OTP_TTL.total_seconds()),
        debug_code=code if settings.ENVIRONMENT == "development" else None,
    )


@router.post("/login", response_model=TokenPair)
async def login(request: InsuredLoginRequest):
    try:
        return insured_auth_service.login(request.email, request.password, request.otp_code)
    except AccountLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Cuenta bloqueada por intentos fallidos hasta {exc.locked_until.isoformat()}.",
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo, contraseña o código incorrectos.",
        )
