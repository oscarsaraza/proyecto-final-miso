"""Autenticación del asegurado con contraseña, código por SMS y huella (HU-MOV-02, HU-MOV-12).

Todo el estado vive en PostgreSQL para que las réplicas vean lo mismo.
"""
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional, Tuple

import jwt
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.core.sms import SmsDeliveryError, SmsSender, get_sms_sender
from app.modules.identity import policy
from app.modules.identity.db_models import (
    InsuredAccountDB,
    InsuredDeviceDB,
    InsuredOtpDB,
    LoginAttemptDB,
    RevokedTokenDB,
)
from app.modules.identity.models import TokenPair

OTP_TTL = timedelta(minutes=5)
REFRESH_TOKEN_TTL = timedelta(days=7)

PURPOSE_LOGIN = "login"
PURPOSE_RESET = "password_reset"

FAILURE_RESULTS = ("bad_password", "bad_code", "bad_device", "unknown_user", "locked")


class InvalidCredentialsError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class WeakPasswordError(Exception):
    pass


class SmsUnavailableError(Exception):
    pass


class AccountLockedError(Exception):
    def __init__(self, locked_until: datetime, retry_after: int):
        super().__init__("Cuenta bloqueada temporalmente")
        self.locked_until = locked_until
        self.retry_after = retry_after


class RateLimitedError(Exception):
    def __init__(self, retry_after: int):
        super().__init__("Demasiadas solicitudes")
        self.retry_after = retry_after


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class InsuredAuthService:
    def __init__(self, clock: Callable[[], datetime] = _utcnow, sms_sender: Optional[SmsSender] = None):
        self._clock = clock
        self._sms = sms_sender

    @property
    def sms(self) -> SmsSender:
        if self._sms is None:
            self._sms = get_sms_sender()
        return self._sms

    async def register(
        self,
        session: AsyncSession,
        *,
        email: str,
        full_name: str,
        document_number: str,
        phone: str,
        password: str,
        user_id: Optional[str] = None,
    ) -> InsuredAccountDB:
        account = InsuredAccountDB(
            user_id=user_id or str(uuid.uuid4()),
            email=email.strip().lower(),
            full_name=full_name,
            document_number=document_number,
            phone=phone,
            password_hash=get_password_hash(password),
            failed_attempts=0,
            lock_count=0,
            token_version=0,
        )
        session.add(account)
        await session.commit()
        return account

    async def seed_default_account(self, session: AsyncSession) -> None:
        if settings.ENVIRONMENT == "production":
            return
        if await self._find(session, "maria.ruiz@correo.co") is None:
            await self.register(
                session,
                user_id="ins-0001",
                email="maria.ruiz@correo.co",
                full_name="María Ruiz",
                document_number="1020304050",
                phone="+573000000000",
                password="Solventa2026!",
            )

    async def request_otp(
        self, session: AsyncSession, email: str, ip: Optional[str] = None, purpose: str = PURPOSE_LOGIN
    ) -> Optional[str]:
        """Genera y envía el código. Devuelve None si el correo no existe (no se revela al cliente)."""
        now = self._clock()
        email = email.strip().lower()
        await self._check_ip(session, ip, now, otp_request=True)

        account = await self._find(session, email)
        if account is None:
            await self._audit(session, email, None, ip, "otp_request", "unknown_user", now)
            await session.commit()
            return None

        requested = await self._attempt_times(session, LoginAttemptDB.user_id == account.user_id, "otp_request", ("success",), now - timedelta(hours=1))
        retry_after = policy.otp_request_retry_after(requested, now)
        if retry_after is not None:
            await self._audit(session, email, account.user_id, ip, "otp_request", "rate_limited", now)
            await session.commit()
            raise RateLimitedError(retry_after)

        code = f"{secrets.randbelow(1_000_000):06d}"
        await session.execute(
            delete(InsuredOtpDB).where(InsuredOtpDB.user_id == account.user_id, InsuredOtpDB.purpose == purpose)
        )
        session.add(
            InsuredOtpDB(
                user_id=account.user_id,
                purpose=purpose,
                code_hash=self._code_hash(account.user_id, purpose, code),
                expires_at=now + OTP_TTL,
                attempts=0,
                created_at=now,
            )
        )
        try:
            await self.sms.send(account.phone, self._sms_body(code, purpose))
        except SmsDeliveryError as exc:
            await session.rollback()
            raise SmsUnavailableError() from exc
        await self._audit(session, email, account.user_id, ip, "otp_request", "success", now)
        await session.commit()
        return code

    async def login(
        self, session: AsyncSession, email: str, password: str, otp_code: str, ip: Optional[str] = None
    ) -> TokenPair:
        now = self._clock()
        email = email.strip().lower()
        await self._check_ip(session, ip, now)

        account = await self._find(session, email, for_update=True)
        if account is None:
            await self._audit(session, email, None, ip, "password", "unknown_user", now)
            await session.commit()
            raise InvalidCredentialsError()

        await self._reject_if_locked(session, account, ip, "password", now)

        if not verify_password(password, account.password_hash):
            await self._register_password_failure(session, account, ip, now)
            raise InvalidCredentialsError()

        if not await self._consume_code(session, account, PURPOSE_LOGIN, otp_code, now):
            await self._audit(session, email, account.user_id, ip, "otp", "bad_code", now)
            await session.commit()
            raise InvalidCredentialsError()

        account.failed_attempts = 0
        account.lock_count = 0
        await self._audit(session, email, account.user_id, ip, "password", "success", now)
        tokens = self._issue_tokens(account)
        await session.commit()
        return tokens

    async def logout(self, session: AsyncSession, refresh_token: str) -> None:
        """Revoca el refresh token (HU-MOV-12). Repetir el logout no falla."""
        claims = self._decode_refresh_token(refresh_token)
        await self._revoke_jti(session, claims)
        await session.commit()

    async def refresh(self, session: AsyncSession, refresh_token: str) -> TokenPair:
        claims = self._decode_refresh_token(refresh_token)
        if await session.get(RevokedTokenDB, claims["jti"]) is not None:
            raise InvalidTokenError()
        account = await session.get(InsuredAccountDB, claims["sub"])
        if account is None or claims.get("ver", 0) != account.token_version:
            raise InvalidTokenError()
        now = self._clock()
        if account.locked_until is not None and now < account.locked_until:
            raise InvalidTokenError()
        await self._revoke_jti(session, claims)
        tokens = self._issue_tokens(account)
        await session.commit()
        return tokens

    async def register_device(self, session: AsyncSession, user_id: str) -> Tuple[str, str]:
        """Vincula el teléfono para ingresar con huella; el secreto solo se entrega una vez."""
        if await session.get(InsuredAccountDB, user_id) is None:
            raise InvalidTokenError()
        device_id = str(uuid.uuid4())
        secret = secrets.token_urlsafe(32)
        session.add(
            InsuredDeviceDB(device_id=device_id, user_id=user_id, secret_hash=_sha256(secret), created_at=self._clock())
        )
        await session.commit()
        return device_id, secret

    async def biometric_login(
        self, session: AsyncSession, device_id: str, device_secret: str, ip: Optional[str] = None
    ) -> TokenPair:
        now = self._clock()
        await self._check_ip(session, ip, now)

        device = await session.get(InsuredDeviceDB, device_id)
        valid = (
            device is not None
            and device.revoked_at is None
            and hmac.compare_digest(device.secret_hash, _sha256(device_secret))
        )
        if not valid:
            await self._audit(session, f"device:{device_id}", device.user_id if device else None, ip, "biometric", "bad_device", now)
            await session.commit()
            raise InvalidCredentialsError()

        account = await session.get(InsuredAccountDB, device.user_id)
        await self._reject_if_locked(session, account, ip, "biometric", now)
        device.last_used_at = now
        await self._audit(session, account.email, account.user_id, ip, "biometric", "success", now)
        tokens = self._issue_tokens(account)
        await session.commit()
        return tokens

    async def revoke_device(self, session: AsyncSession, user_id: str, device_id: str) -> None:
        await session.execute(
            update(InsuredDeviceDB)
            .where(
                InsuredDeviceDB.device_id == device_id,
                InsuredDeviceDB.user_id == user_id,
                InsuredDeviceDB.revoked_at.is_(None),
            )
            .values(revoked_at=self._clock())
        )
        await session.commit()

    async def forgot_password(self, session: AsyncSession, email: str, ip: Optional[str] = None) -> Optional[str]:
        return await self.request_otp(session, email, ip, purpose=PURPOSE_RESET)

    async def reset_password(
        self, session: AsyncSession, email: str, code: str, new_password: str, ip: Optional[str] = None
    ) -> None:
        """Cambia la contraseña, quita el bloqueo, cierra todas las sesiones y desvincula las huellas."""
        if not policy.is_strong_password(new_password):
            raise WeakPasswordError()
        now = self._clock()
        email = email.strip().lower()
        await self._check_ip(session, ip, now)

        account = await self._find(session, email, for_update=True)
        if account is None:
            await self._audit(session, email, None, ip, "reset", "unknown_user", now)
            await session.commit()
            raise InvalidCredentialsError()

        if not await self._consume_code(session, account, PURPOSE_RESET, code, now):
            await self._audit(session, email, account.user_id, ip, "reset", "bad_code", now)
            await session.commit()
            raise InvalidCredentialsError()

        account.password_hash = get_password_hash(new_password)
        account.failed_attempts = 0
        account.lock_count = 0
        account.locked_until = None
        account.token_version += 1
        await session.execute(
            update(InsuredDeviceDB)
            .where(InsuredDeviceDB.user_id == account.user_id, InsuredDeviceDB.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self._audit(session, email, account.user_id, ip, "reset", "success", now)
        await session.commit()

    async def _find(self, session: AsyncSession, email: str, for_update: bool = False) -> Optional[InsuredAccountDB]:
        stmt = select(InsuredAccountDB).where(InsuredAccountDB.email == email.strip().lower())
        if for_update:
            stmt = stmt.with_for_update()
        return (await session.execute(stmt)).scalars().first()

    async def _reject_if_locked(
        self, session: AsyncSession, account: InsuredAccountDB, ip: Optional[str], channel: str, now: datetime
    ) -> None:
        if account.locked_until is not None and now < account.locked_until:
            await self._audit(session, account.email, account.user_id, ip, channel, "locked", now)
            await session.commit()
            raise AccountLockedError(account.locked_until, policy.seconds_until(account.locked_until, now))

    async def _register_password_failure(
        self, session: AsyncSession, account: InsuredAccountDB, ip: Optional[str], now: datetime
    ) -> None:
        account.lock_count = policy.effective_lock_count(account.lock_count, account.locked_until, now)
        account.failed_attempts += 1
        await self._audit(session, account.email, account.user_id, ip, "password", "bad_password", now)
        if account.failed_attempts >= policy.MAX_PASSWORD_FAILURES:
            account.failed_attempts = 0
            account.lock_count += 1
            account.locked_until = now + policy.lock_duration(account.lock_count)
            await session.execute(delete(InsuredOtpDB).where(InsuredOtpDB.user_id == account.user_id))
            await session.commit()
            raise AccountLockedError(account.locked_until, policy.seconds_until(account.locked_until, now))
        await session.commit()

    async def _consume_code(
        self, session: AsyncSession, account: InsuredAccountDB, purpose: str, code: str, now: datetime
    ) -> bool:
        """Un código equivocado no bloquea la cuenta: al tercer fallo se descarta y hay que pedir otro."""
        stmt = (
            select(InsuredOtpDB)
            .where(InsuredOtpDB.user_id == account.user_id, InsuredOtpDB.purpose == purpose)
            .with_for_update()
        )
        otp = (await session.execute(stmt)).scalars().first()
        if otp is None:
            return False
        if now > otp.expires_at:
            await session.delete(otp)
            return False
        if not hmac.compare_digest(otp.code_hash, self._code_hash(account.user_id, purpose, code)):
            otp.attempts += 1
            if otp.attempts >= policy.MAX_CODE_ATTEMPTS:
                await session.delete(otp)
            return False
        await session.delete(otp)
        return True

    async def _check_ip(self, session: AsyncSession, ip: Optional[str], now: datetime, otp_request: bool = False) -> None:
        if not ip:
            return
        if otp_request:
            times = await self._attempt_times(session, LoginAttemptDB.ip == ip, "otp_request", None, now - policy.IP_WINDOW)
            retry_after = policy.window_retry_after(times, policy.IP_MAX_OTP_REQUESTS, now)
        else:
            times = await self._attempt_times(session, LoginAttemptDB.ip == ip, None, FAILURE_RESULTS, now - policy.IP_WINDOW)
            retry_after = policy.window_retry_after(times, policy.IP_MAX_LOGIN_FAILURES, now)
        if retry_after is not None:
            raise RateLimitedError(retry_after)

    async def _attempt_times(
        self,
        session: AsyncSession,
        subject_filter,
        channel: Optional[str],
        results: Optional[Tuple[str, ...]],
        since: datetime,
    ) -> List[datetime]:
        stmt = select(LoginAttemptDB.created_at).where(subject_filter, LoginAttemptDB.created_at > since)
        if channel is not None:
            stmt = stmt.where(LoginAttemptDB.channel == channel)
        if results is not None:
            stmt = stmt.where(LoginAttemptDB.result.in_(results))
        return list((await session.execute(stmt)).scalars().all())

    async def _audit(
        self,
        session: AsyncSession,
        email: str,
        user_id: Optional[str],
        ip: Optional[str],
        channel: str,
        result: str,
        now: datetime,
    ) -> None:
        session.add(
            LoginAttemptDB(email=email[:254], user_id=user_id, ip=ip, channel=channel, result=result, created_at=now)
        )

    async def _revoke_jti(self, session: AsyncSession, claims: dict) -> None:
        if await session.get(RevokedTokenDB, claims["jti"]) is None:
            session.add(
                RevokedTokenDB(jti=claims["jti"], expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc))
            )

    @staticmethod
    def _code_hash(user_id: str, purpose: str, code: str) -> str:
        message = f"{user_id}:{purpose}:{code}".encode()
        return hmac.new(settings.JWT_SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()

    @staticmethod
    def _sms_body(code: str, purpose: str) -> str:
        if purpose == PURPOSE_RESET:
            return f"Solventa: su código para cambiar la contraseña es {code}. Vence en 5 minutos. No lo comparta."
        return f"Solventa: su código es {code}. Vence en 5 minutos. No lo comparta."

    @staticmethod
    def _decode_refresh_token(token: str) -> dict:
        try:
            claims = decode_access_token(token)
        except jwt.PyJWTError:
            raise InvalidTokenError()
        if claims.get("type") != "refresh" or not claims.get("jti"):
            raise InvalidTokenError()
        return claims

    def _issue_tokens(self, account: InsuredAccountDB) -> TokenPair:
        access_token = create_access_token(
            subject=account.user_id,
            role="insured",
            claims={"channel": "mobile", "type": "access", "ver": account.token_version},
        )
        refresh_token = create_access_token(
            subject=account.user_id,
            role="insured",
            claims={"channel": "mobile", "type": "refresh", "jti": uuid.uuid4().hex, "ver": account.token_version},
            expires_delta=REFRESH_TOKEN_TTL,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            full_name=account.full_name,
        )


insured_auth_service = InsuredAuthService()
