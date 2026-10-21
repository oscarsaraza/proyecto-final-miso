"""Router BFF de autenticación del asegurado para la app móvil (HU-MOV-02, HU-MOV-12)."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import require_roles
from app.modules.identity import policy
from app.modules.identity.models import (
    BiometricLoginRequest,
    DeviceRegistrationResponse,
    InsuredLoginRequest,
    LockedResponse,
    MessageResponse,
    OtpRequest,
    OtpResponse,
    PasswordForgotRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenPair,
)
from app.modules.identity.service import (
    OTP_TTL,
    AccountLockedError,
    InvalidCredentialsError,
    InvalidTokenError,
    RateLimitedError,
    SamePasswordError,
    SmsUnavailableError,
    WeakPasswordError,
    insured_auth_service,
)

router = APIRouter(prefix="/auth", tags=["Auth Asegurado"])

require_insured = require_roles(["insured"])

INVALID_CREDENTIALS = "Los datos ingresados no son válidos."
CODE_SENT = "Si el correo está registrado, enviamos un código por SMS."
LOCKED_RESPONSES: Dict[int | str, Dict[str, Any]] = {423: {"model": LockedResponse}}


def _client_ip(request: Request) -> str | None:
    return policy.client_ip(request.headers, request.client.host if request.client else None)


def _locked(exc: AccountLockedError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_423_LOCKED,
        headers={"Retry-After": str(exc.retry_after)},
        content={
            "detail": "Por seguridad, el ingreso está suspendido temporalmente.",
            "locked_until": exc.locked_until.isoformat(),
            "retry_after": exc.retry_after,
        },
    )


def _rate_limited(exc: RateLimitedError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Demasiadas solicitudes. Espere antes de intentar de nuevo.",
        headers={"Retry-After": str(exc.retry_after)},
    )


def _sms_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="No pudimos enviar el código. Intente en unos minutos.",
    )


def _otp_response(code: str | None) -> OtpResponse:
    expose = insured_auth_service.sms.exposes_code and settings.ENVIRONMENT != "production"
    return OtpResponse(
        message=CODE_SENT,
        expires_in=int(OTP_TTL.total_seconds()),
        debug_code=code if expose else None,
    )


@router.post("/otp", response_model=OtpResponse)
async def request_otp(request: OtpRequest, http: Request, db: AsyncSession = Depends(get_db_session)):
    try:
        code = await insured_auth_service.request_otp(db, request.email, _client_ip(http))
    except RateLimitedError as exc:
        raise _rate_limited(exc)
    except SmsUnavailableError:
        raise _sms_unavailable()
    return _otp_response(code)


@router.post("/login", response_model=TokenPair, responses=LOCKED_RESPONSES)
async def login(request: InsuredLoginRequest, http: Request, db: AsyncSession = Depends(get_db_session)):
    try:
        return await insured_auth_service.login(
            db, request.email, request.password, request.otp_code, _client_ip(http)
        )
    except AccountLockedError as exc:
        return _locked(exc)
    except RateLimitedError as exc:
        raise _rate_limited(exc)
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db_session)):
    try:
        await insured_auth_service.logout(db, request.refresh_token)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de sesión inválido.")


@router.post("/refresh", response_model=TokenPair)
async def refresh(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db_session)):
    try:
        return await insured_auth_service.refresh(db, request.refresh_token)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión revocada o vencida.")


@router.post("/devices", response_model=DeviceRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    claims: Dict[str, Any] = Depends(require_insured), db: AsyncSession = Depends(get_db_session)
):
    try:
        device_id, secret = await insured_auth_service.register_device(db, claims["sub"])
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida.")
    return DeviceRegistrationResponse(device_id=device_id, device_secret=secret)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device(
    device_id: str, claims: Dict[str, Any] = Depends(require_insured), db: AsyncSession = Depends(get_db_session)
):
    await insured_auth_service.revoke_device(db, claims["sub"], device_id)


@router.post("/biometric", response_model=TokenPair, responses=LOCKED_RESPONSES)
async def biometric_login(request: BiometricLoginRequest, http: Request, db: AsyncSession = Depends(get_db_session)):
    try:
        return await insured_auth_service.biometric_login(
            db, request.device_id, request.device_secret, _client_ip(http)
        )
    except AccountLockedError as exc:
        return _locked(exc)
    except RateLimitedError as exc:
        raise _rate_limited(exc)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El ingreso con huella ya no es válido en este teléfono.",
        )


@router.post("/password/forgot", response_model=OtpResponse)
async def forgot_password(request: PasswordForgotRequest, http: Request, db: AsyncSession = Depends(get_db_session)):
    try:
        code = await insured_auth_service.forgot_password(db, request.email, _client_ip(http))
    except RateLimitedError as exc:
        raise _rate_limited(exc)
    except SmsUnavailableError:
        raise _sms_unavailable()
    return _otp_response(code)


@router.post("/password/reset", response_model=MessageResponse)
async def reset_password(request: PasswordResetRequest, http: Request, db: AsyncSession = Depends(get_db_session)):
    try:
        await insured_auth_service.reset_password(
            db, request.email, request.code, request.new_password, _client_ip(http)
        )
    except WeakPasswordError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"La contraseña debe tener al menos {policy.MIN_PASSWORD_LENGTH} caracteres, con letras y números.",
        )
    except RateLimitedError as exc:
        raise _rate_limited(exc)
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS)
    except SamePasswordError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La contraseña no es válida. Elija una diferente.",
        )
    return MessageResponse(message="Contraseña actualizada. Ingrese con su nueva contraseña.")
