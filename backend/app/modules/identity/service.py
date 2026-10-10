"""Autenticación del asegurado con contraseña y código de un solo uso (HU-MOV-02 / ESC-SEG-01)."""
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Optional, Set

import jwt

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.modules.identity.models import TokenPair

MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION = timedelta(minutes=15)
OTP_TTL = timedelta(minutes=5)
REFRESH_TOKEN_TTL = timedelta(days=7)


class InvalidCredentialsError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class AccountLockedError(Exception):
    def __init__(self, locked_until: datetime):
        super().__init__("Cuenta bloqueada temporalmente")
        self.locked_until = locked_until


@dataclass
class InsuredAccount:
    user_id: str
    email: str
    full_name: str
    document_number: str
    password_hash: str
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None


@dataclass
class OtpChallenge:
    code: str
    expires_at: datetime


class InsuredAuthService:
    def __init__(self, clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self._clock = clock
        self._accounts: Dict[str, InsuredAccount] = {}
        self._otps: Dict[str, OtpChallenge] = {}
        self._revoked_jtis: Set[str] = set()

    def register(self, account: InsuredAccount) -> None:
        self._accounts[account.email.lower()] = account

    def request_otp(self, email: str) -> Optional[str]:
        """Genera el código que se enviaría por SMS. None si el correo no existe (no se revela al cliente)."""
        account = self._accounts.get(email.lower())
        if account is None:
            return None
        code = f"{secrets.randbelow(1_000_000):06d}"
        self._otps[account.email.lower()] = OtpChallenge(code=code, expires_at=self._clock() + OTP_TTL)
        return code

    def login(self, email: str, password: str, otp_code: str) -> TokenPair:
        account = self._accounts.get(email.lower())
        if account is None:
            raise InvalidCredentialsError()

        now = self._clock()
        if account.locked_until is not None:
            if now < account.locked_until:
                raise AccountLockedError(account.locked_until)
            account.locked_until = None
            account.failed_attempts = 0

        if not (verify_password(password, account.password_hash) and self._consume_otp(account, otp_code, now)):
            account.failed_attempts += 1
            if account.failed_attempts >= MAX_FAILED_ATTEMPTS:
                account.locked_until = now + LOCKOUT_DURATION
                raise AccountLockedError(account.locked_until)
            raise InvalidCredentialsError()

        account.failed_attempts = 0
        return self._issue_tokens(account)

    def logout(self, refresh_token: str) -> None:
        """Revoca el refresh token (HU-MOV-12). Repetir el logout no falla."""
        self._revoked_jtis.add(self._decode_refresh_token(refresh_token)["jti"])

    def refresh(self, refresh_token: str) -> TokenPair:
        claims = self._decode_refresh_token(refresh_token)
        if claims["jti"] in self._revoked_jtis:
            raise InvalidTokenError()
        account = next((a for a in self._accounts.values() if a.user_id == claims["sub"]), None)
        if account is None:
            raise InvalidTokenError()
        self._revoked_jtis.add(claims["jti"])
        return self._issue_tokens(account)

    def reset_state(self) -> None:
        self._otps.clear()
        self._revoked_jtis.clear()
        for account in self._accounts.values():
            account.failed_attempts = 0
            account.locked_until = None

    def _consume_otp(self, account: InsuredAccount, otp_code: str, now: datetime) -> bool:
        challenge = self._otps.get(account.email.lower())
        if challenge is None or now > challenge.expires_at:
            return False
        if not hmac.compare_digest(challenge.code, otp_code):
            return False
        del self._otps[account.email.lower()]
        return True

    @staticmethod
    def _decode_refresh_token(token: str) -> dict:
        try:
            claims = decode_access_token(token)
        except jwt.PyJWTError:
            raise InvalidTokenError()
        if claims.get("type") != "refresh" or not claims.get("jti"):
            raise InvalidTokenError()
        return claims

    def _issue_tokens(self, account: InsuredAccount) -> TokenPair:
        access_token = create_access_token(
            subject=account.user_id,
            role="insured",
            claims={"channel": "mobile", "type": "access"},
        )
        refresh_token = create_access_token(
            subject=account.user_id,
            role="insured",
            claims={"channel": "mobile", "type": "refresh", "jti": uuid.uuid4().hex},
            expires_delta=REFRESH_TOKEN_TTL,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            full_name=account.full_name,
        )


insured_auth_service = InsuredAuthService()

if settings.ENVIRONMENT != "production":
    insured_auth_service.register(
        InsuredAccount(
            user_id="ins-0001",
            email="maria.ruiz@correo.co",
            full_name="María Ruiz",
            document_number="1020304050",
            password_hash=get_password_hash("Solventa2026!"),
        )
    )
