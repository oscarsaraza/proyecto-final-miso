"""Seguridad, hashing, TOTP y tokens JWT (HU-WEB-13)."""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import struct
import time
from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
import jwt
from app.core.config import settings

# bcrypt directo: passlib 1.7.4 falla con bcrypt >= 4.1 al detectar el "wrap bug".
security_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash bcrypt almacenado."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Genera hash bcrypt seguro de la contraseña."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def validate_password_strength(password: str) -> bool:
    """
    Valida política de contraseña fuerte (HA-06):
    - Al menos 8 caracteres.
    - Al menos una letra mayúscula.
    - Al menos una letra minúscula.
    - Al menos un dígito numérico.
    - Al menos un caracter especial.
    """
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/~`" for c in password)
    return has_upper and has_lower and has_digit and has_special


def generate_totp(
    secret: str,
    timestamp: Optional[int] = None,
    time_step: int = 30,
    digits: int = 6,
) -> str:
    """
    Genera código TOTP conforme a RFC 6238 a partir de un secreto Base32.
    """
    if timestamp is None:
        timestamp = int(time.time())
    secret_clean = secret.strip().replace(" ", "").upper()
    padding = (8 - len(secret_clean) % 8) % 8
    secret_padded = secret_clean + ("=" * padding)
    key = base64.b32decode(secret_padded, casefold=True)

    counter = int(timestamp // time_step)
    counter_bytes = struct.pack(">Q", counter)

    hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0F
    truncated_hash = struct.unpack(">I", hmac_hash[offset : offset + 4])[0]
    truncated_hash &= 0x7FFFFFFF
    code = str(truncated_hash % (10**digits)).zfill(digits)
    return code


def verify_totp(
    secret: str,
    code: str,
    timestamp: Optional[int] = None,
    tolerance_steps: int = 1,
    time_step: int = 30,
    digits: int = 6,
) -> bool:
    """
    Valida código TOTP con ventana de tolerancia de ±30 segundos (HA-06).
    tolerance_steps=1 permite la ventana actual, -30s y +30s.
    """
    if not code or len(code.strip()) != digits or not code.strip().isdigit():
        return False
    if timestamp is None:
        timestamp = int(time.time())

    code_clean = code.strip()
    current_step = int(timestamp // time_step)

    for step_offset in range(-tolerance_steps, tolerance_steps + 1):
        step_time = (current_step + step_offset) * time_step
        expected_code = generate_totp(
            secret,
            timestamp=step_time,
            time_step=time_step,
            digits=digits,
        )
        if hmac.compare_digest(expected_code, code_clean):
            return True
    return False


def create_access_token(
    subject: str,
    role: str,
    claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Genera token de acceso JWT con claims auditables de rol y expiración."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if claims:
        to_encode.update(claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Genera token de refresco JWT con vigencia extendida."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodifica y valida un token JWT usando la clave y algoritmo configurados."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """Decodifica y valida un token de refresco JWT."""
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Token no es de tipo refresh")
    return payload


def require_roles(allowed_roles: List[str]):
    """
    Dependencia de autorización basada en roles (RBAC / HA-13).
    Valida firma, expiración, tipo de token 'access' y claim 'role' en el Bearer token.
    """
    async def role_checker(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    ) -> Dict[str, Any]:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticación requerido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            payload = decode_access_token(credentials.credentials)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de acceso expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de acceso inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_type = payload.get("type", "access")
        if token_type == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de refresco no permitido como token de acceso",
                headers={"WWW-Authenticate": "Bearer"},
            )

        role = payload.get("role")
        if not role or role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes para acceder a este recurso",
            )
        return payload

    return role_checker
